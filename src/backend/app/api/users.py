import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.assessment import AggregatedScore, AssessmentCampaign
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])

ERROR_MAP = {
    "not_found": (status.HTTP_404_NOT_FOUND, "Пользователь не найден"),
    "email_taken": (status.HTTP_409_CONFLICT, "Email уже занят"),
    "forbidden": (status.HTTP_403_FORBIDDEN, "Недостаточно прав"),
    "weak_password": (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Пароль не соответствует требованиям",
    ),
}


def _raise(code: str) -> None:
    status_code, detail = ERROR_MAP.get(code, (400, code))
    raise HTTPException(status_code=status_code, detail=detail)


@router.get("", response_model=list[UserRead])
async def list_users(
    search: str | None = Query(None),
    department_id: uuid.UUID | None = Query(None),
    team_id: uuid.UUID | None = Query(None),
    role: UserRole | None = Query(None),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    return await service.list_users(
        current_user,
        search=search,
        department_id=department_id,
        team_id=team_id,
        role=role,
        is_active=is_active,
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "hr", "head")),
):
    service = UserService(db)
    try:
        user = await service.create(data)
    except ValueError as e:
        _raise(str(e))
    return user


@router.get("/me", response_model=UserRead)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    return await service.get_by_id(current_user.id)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    try:
        user = await service.get_by_id(user_id)
    except ValueError as e:
        _raise(str(e))

    if current_user.role == UserRole.EMPLOYEE and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    try:
        user = await service.update(user_id, data, current_user)
    except ValueError as e:
        _raise(str(e))
    return user


@router.post("/{user_id}/activate", response_model=UserRead)
async def activate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "hr")),
):
    service = UserService(db)
    try:
        user = await service.activate(user_id)
    except ValueError as e:
        _raise(str(e))
    return user


@router.post("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "hr")),
):
    service = UserService(db)
    try:
        user = await service.deactivate(user_id)
    except ValueError as e:
        _raise(str(e))
    return user


@router.get("/{user_id}/assessment-history")
async def get_assessment_history(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    elevated = ("admin", "head", "department_head", "team_lead", "hr")
    if current_user.role.value not in elevated and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    result = await db.execute(
        select(AggregatedScore, AssessmentCampaign)
        .join(AssessmentCampaign, AggregatedScore.campaign_id == AssessmentCampaign.id)
        .where(AggregatedScore.user_id == user_id)
        .order_by(AssessmentCampaign.end_date.desc())
    )
    rows = result.all()
    return [
        {
            "campaign_id": str(agg.campaign_id),
            "campaign_name": campaign.name,
            "campaign_end_date": str(campaign.end_date),
            "competency_id": str(agg.competency_id),
            "final_score": float(agg.final_score),
            "self_score": float(agg.self_score) if agg.self_score is not None else None,
            "tl_score": float(agg.tl_score) if agg.tl_score is not None else None,
            "dh_score": float(agg.dh_score) if agg.dh_score is not None else None,
            "peer_score": float(agg.peer_score) if agg.peer_score is not None else None,
        }
        for agg, campaign in rows
    ]
