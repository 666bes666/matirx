import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.development_plan import (
    DevelopmentGoalCreate,
    DevelopmentGoalRead,
    DevelopmentGoalUpdate,
    DevelopmentPlanCreate,
    DevelopmentPlanRead,
    DevelopmentPlanUpdate,
)
from app.services.development_plan import DevelopmentPlanService

router = APIRouter(prefix="/development-plans", tags=["development-plans"])

ERROR_MAP = {
    "not_found": (status.HTTP_404_NOT_FOUND, "ИПР не найден"),
    "goal_not_found": (status.HTTP_404_NOT_FOUND, "Цель не найдена"),
    "resource_not_found": (status.HTTP_404_NOT_FOUND, "Ресурс не найден"),
}


def _raise(key: str):
    code, msg = ERROR_MAP.get(key, (status.HTTP_400_BAD_REQUEST, key))
    raise HTTPException(status_code=code, detail=msg)


@router.get("", response_model=list[DevelopmentPlanRead])
async def list_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await DevelopmentPlanService(db).list_plans(current_user)


@router.post("", response_model=DevelopmentPlanRead, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: DevelopmentPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "head", "department_head", "team_lead")),
):
    return await DevelopmentPlanService(db).create_plan(data, current_user)


@router.get("/{plan_id}", response_model=DevelopmentPlanRead)
async def get_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return await DevelopmentPlanService(db).get_plan(plan_id)
    except ValueError as e:
        _raise(str(e))


@router.patch("/{plan_id}", response_model=DevelopmentPlanRead)
async def update_plan(
    plan_id: uuid.UUID,
    data: DevelopmentPlanUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head", "team_lead")),
):
    try:
        return await DevelopmentPlanService(db).update_plan(plan_id, data)
    except ValueError as e:
        _raise(str(e))


@router.post("/{plan_id}/archive")
async def archive_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head", "team_lead")),
):
    try:
        await DevelopmentPlanService(db).archive_plan(plan_id)
        return {"ok": True}
    except ValueError as e:
        _raise(str(e))


@router.post(
    "/{plan_id}/goals",
    response_model=DevelopmentGoalRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_goal(
    plan_id: uuid.UUID,
    data: DevelopmentGoalCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head", "team_lead")),
):
    try:
        return await DevelopmentPlanService(db).add_goal(plan_id, data)
    except ValueError as e:
        _raise(str(e))


@router.patch("/{plan_id}/goals/{goal_id}", response_model=DevelopmentGoalRead)
async def update_goal(
    plan_id: uuid.UUID,
    goal_id: uuid.UUID,
    data: DevelopmentGoalUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return await DevelopmentPlanService(db).update_goal(goal_id, data)
    except ValueError as e:
        _raise(str(e))


@router.delete("/{plan_id}/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    plan_id: uuid.UUID,
    goal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head", "team_lead")),
):
    try:
        await DevelopmentPlanService(db).delete_goal(goal_id)
    except ValueError as e:
        _raise(str(e))
