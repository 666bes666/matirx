import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.assessment import AggregatedScore
from app.models.competency import Competency
from app.models.department import Department
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/matrix")
async def get_matrix(
    department_id: uuid.UUID | None = Query(None),
    team_id: uuid.UUID | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users_query = (
        select(User)
        .options(selectinload(User.department), selectinload(User.team))
        .where(User.is_active.is_(True))
    )

    if current_user.role == UserRole.TEAM_LEAD:
        users_query = users_query.where(User.team_id == current_user.team_id)
    elif current_user.role == UserRole.DEPARTMENT_HEAD:
        users_query = users_query.where(User.department_id == current_user.department_id)
    elif current_user.role == UserRole.EMPLOYEE:
        users_query = users_query.where(User.id == current_user.id)

    if department_id is not None:
        users_query = users_query.where(User.department_id == department_id)
    if team_id is not None:
        users_query = users_query.where(User.team_id == team_id)

    users_result = await db.execute(users_query)
    users = list(users_result.scalars().all())

    comp_query = select(Competency).where(Competency.is_archived.is_(False))
    if category_id is not None:
        comp_query = comp_query.where(Competency.category_id == category_id)
    comp_query = comp_query.order_by(Competency.name)
    comp_result = await db.execute(comp_query)
    competencies = list(comp_result.scalars().all())

    user_ids = [u.id for u in users]
    comp_ids = [c.id for c in competencies]

    scores: dict[uuid.UUID, dict[uuid.UUID, float]] = {}
    if user_ids and comp_ids:
        agg_result = await db.execute(
            select(AggregatedScore).where(
                AggregatedScore.user_id.in_(user_ids),
                AggregatedScore.competency_id.in_(comp_ids),
            )
        )
        for agg in agg_result.scalars().all():
            if agg.user_id not in scores:
                scores[agg.user_id] = {}
            scores[agg.user_id][agg.competency_id] = float(agg.final_score)

    return {
        "users": [
            {
                "id": str(u.id),
                "full_name": f"{u.last_name} {u.first_name}",
                "department": u.department.name if u.department else None,
                "team": u.team.name if u.team else None,
            }
            for u in users
        ],
        "competencies": [
            {
                "id": str(c.id),
                "name": c.name,
                "category_id": str(c.category_id),
            }
            for c in competencies
        ],
        "scores": {
            str(uid): {str(cid): score for cid, score in cscores.items()}
            for uid, cscores in scores.items()
        },
    }


@router.get("/heatmap")
async def get_heatmap(
    category_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    comp_query = (
        select(Competency)
        .where(Competency.is_archived.is_(False))
        .order_by(Competency.name)
    )
    if category_id is not None:
        comp_query = comp_query.where(Competency.category_id == category_id)
    comp_result = await db.execute(comp_query)
    competencies = list(comp_result.scalars().all())

    dept_result = await db.execute(
        select(Department).order_by(Department.sort_order, Department.name)
    )
    departments = list(dept_result.scalars().all())

    users_result = await db.execute(
        select(User)
        .options(selectinload(User.department))
        .where(User.is_active.is_(True), User.department_id.isnot(None))
    )
    users = list(users_result.scalars().all())

    dept_user_ids: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    for u in users:
        if u.department_id is not None:
            dept_user_ids[u.department_id].append(u.id)

    all_user_ids = [u.id for u in users]
    comp_ids = [c.id for c in competencies]

    user_scores: dict[uuid.UUID, dict[uuid.UUID, float]] = defaultdict(dict)
    if all_user_ids and comp_ids:
        agg_result = await db.execute(
            select(AggregatedScore).where(
                AggregatedScore.user_id.in_(all_user_ids),
                AggregatedScore.competency_id.in_(comp_ids),
            )
        )
        for agg in agg_result.scalars().all():
            user_scores[agg.user_id][agg.competency_id] = float(agg.final_score)

    averages: dict[str, dict[str, float | None]] = {}
    for dept in departments:
        dept_str = str(dept.id)
        averages[dept_str] = {}
        uids = dept_user_ids.get(dept.id, [])
        for comp in competencies:
            comp_str = str(comp.id)
            vals = [
                user_scores[uid][comp.id]
                for uid in uids
                if comp.id in user_scores[uid]
            ]
            averages[dept_str][comp_str] = round(sum(vals) / len(vals), 2) if vals else None

    return {
        "departments": [{"id": str(d.id), "name": d.name} for d in departments],
        "competencies": [
            {"id": str(c.id), "name": c.name, "category_id": str(c.category_id)}
            for c in competencies
        ],
        "averages": averages,
    }
