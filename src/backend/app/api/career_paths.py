import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.career_path import (
    CareerPathCreate,
    CareerPathRead,
    CareerPathRequirementInput,
    CareerReadinessRead,
)
from app.services.career_path import CareerPathService

router = APIRouter(prefix="/career-paths", tags=["career-paths"])

ERROR_MAP = {
    "not_found": (status.HTTP_404_NOT_FOUND, "Карьерный путь не найден"),
    "already_exists": (status.HTTP_409_CONFLICT, "Такой карьерный путь уже существует"),
}


def _raise(key: str):
    code, msg = ERROR_MAP.get(key, (status.HTTP_400_BAD_REQUEST, key))
    raise HTTPException(status_code=code, detail=msg)


@router.get("", response_model=list[CareerPathRead])
async def list_paths(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await CareerPathService(db).list_paths()


@router.post("", response_model=CareerPathRead, status_code=status.HTTP_201_CREATED)
async def create_path(
    data: CareerPathCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head")),
):
    try:
        return await CareerPathService(db).create_path(data)
    except ValueError as e:
        _raise(str(e))


@router.get("/by-department/{department_id}", response_model=list[CareerPathRead])
async def list_paths_for_department(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await CareerPathService(db).list_paths_for_department(department_id)


@router.get("/{path_id}", response_model=CareerPathRead)
async def get_path(
    path_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return await CareerPathService(db).get_path(path_id)
    except ValueError as e:
        _raise(str(e))


@router.delete("/{path_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_path(
    path_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head")),
):
    try:
        await CareerPathService(db).delete_path(path_id)
    except ValueError as e:
        _raise(str(e))


@router.put("/{path_id}/requirements", response_model=CareerPathRead)
async def set_requirements(
    path_id: uuid.UUID,
    requirements: list[CareerPathRequirementInput],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head")),
):
    try:
        return await CareerPathService(db).set_requirements(path_id, requirements)
    except ValueError as e:
        _raise(str(e))


@router.get("/{path_id}/readiness/{user_id}", response_model=CareerReadinessRead)
async def get_readiness(
    path_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    elevated = ("admin", "head", "department_head", "team_lead", "hr")
    if current_user.role.value not in elevated and current_user.id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав")
    try:
        return await CareerPathService(db).get_readiness(path_id, user_id)
    except ValueError as e:
        _raise(str(e))
