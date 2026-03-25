import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import check_department_access, get_current_user, require_roles
from app.models.user import User
from app.schemas.target_profile import (
    TargetProfileCompetencyInput,
    TargetProfileCreate,
    TargetProfileRead,
    TargetProfileUpdate,
)
from app.services.target_profile import TargetProfileService

router = APIRouter(prefix="/target-profiles", tags=["target-profiles"])

ERROR_MAP = {
    "not_found": (status.HTTP_404_NOT_FOUND, "Не найдено"),
    "name_taken": (status.HTTP_409_CONFLICT, "Профиль с такой позицией уже существует"),
}


def _raise(code: str) -> None:
    status_code, detail = ERROR_MAP.get(code, (400, code))
    raise HTTPException(status_code=status_code, detail=detail)


@router.get("", response_model=list[TargetProfileRead])
async def list_target_profiles(
    department_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = TargetProfileService(db)
    return await service.list_by_dept(department_id)


@router.post("", response_model=TargetProfileRead, status_code=status.HTTP_201_CREATED)
async def create_target_profile(
    data: TargetProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "head", "department_head")),
):
    check_department_access(current_user, data.department_id)
    service = TargetProfileService(db)
    try:
        profile = await service.create(data)
    except ValueError as e:
        _raise(str(e))
    return profile


@router.get("/{profile_id}", response_model=TargetProfileRead)
async def get_target_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = TargetProfileService(db)
    try:
        profile = await service.get_by_id(profile_id)
    except ValueError as e:
        _raise(str(e))
    return profile


@router.patch("/{profile_id}", response_model=TargetProfileRead)
async def update_target_profile(
    profile_id: uuid.UUID,
    data: TargetProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "head", "department_head")),
):
    service = TargetProfileService(db)
    try:
        existing = await service.get_by_id(profile_id)
    except ValueError as e:
        _raise(str(e))
    check_department_access(current_user, existing.department_id)
    try:
        profile = await service.update(profile_id, data)
    except ValueError as e:
        _raise(str(e))
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head")),
):
    service = TargetProfileService(db)
    try:
        await service.delete(profile_id)
    except ValueError as e:
        _raise(str(e))


@router.put("/{profile_id}/competencies", response_model=TargetProfileRead)
async def set_competencies(
    profile_id: uuid.UUID,
    competencies: list[TargetProfileCompetencyInput],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "head", "department_head")),
):
    service = TargetProfileService(db)
    try:
        existing = await service.get_by_id(profile_id)
    except ValueError as e:
        _raise(str(e))
    check_department_access(current_user, existing.department_id)
    try:
        profile = await service.set_competencies(profile_id, competencies)
    except ValueError as e:
        _raise(str(e))
    return profile


@router.get("/{profile_id}/gap/{user_id}")
async def get_gap(
    profile_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head", "hr")),
):
    service = TargetProfileService(db)
    try:
        gap = await service.get_gap(profile_id, user_id)
    except ValueError as e:
        _raise(str(e))
    return gap
