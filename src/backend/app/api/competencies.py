import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.competency import (
    CompetencyCategoryRead,
    CompetencyCreate,
    CompetencyRead,
    CompetencyUpdate,
    CriteriaUpsert,
)
from app.services.competency import CompetencyService

router = APIRouter(prefix="/competencies", tags=["competencies"])

ERROR_MAP = {
    "not_found": (status.HTTP_404_NOT_FOUND, "Компетенция не найдена"),
    "category_not_found": (status.HTTP_404_NOT_FOUND, "Категория не найдена"),
    "name_taken": (status.HTTP_409_CONFLICT, "Компетенция с таким именем уже существует"),
}


def _raise(code: str) -> None:
    status_code, detail = ERROR_MAP.get(code, (400, code))
    raise HTTPException(status_code=status_code, detail=detail)


@router.get("/categories", response_model=list[CompetencyCategoryRead])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = CompetencyService(db)
    return await service.list_categories()


@router.get("", response_model=list[CompetencyRead])
async def list_competencies(
    category_id: uuid.UUID | None = Query(None),
    department_id: uuid.UUID | None = Query(None),
    is_common: bool | None = Query(None),
    is_archived: bool | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = CompetencyService(db)
    return await service.list_competencies(
        category_id=category_id,
        department_id=department_id,
        is_common=is_common,
        is_archived=is_archived,
        search=search,
    )


@router.post("", response_model=CompetencyRead, status_code=status.HTTP_201_CREATED)
async def create_competency(
    data: CompetencyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head")),
):
    service = CompetencyService(db)
    try:
        return await service.create(data)
    except ValueError as e:
        _raise(str(e))


@router.get("/{competency_id}", response_model=CompetencyRead)
async def get_competency(
    competency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = CompetencyService(db)
    try:
        return await service.get_by_id(competency_id)
    except ValueError as e:
        _raise(str(e))


@router.patch("/{competency_id}", response_model=CompetencyRead)
async def update_competency(
    competency_id: uuid.UUID,
    data: CompetencyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head")),
):
    service = CompetencyService(db)
    try:
        return await service.update(competency_id, data)
    except ValueError as e:
        _raise(str(e))


@router.post("/{competency_id}/archive", response_model=CompetencyRead)
async def archive_competency(
    competency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head")),
):
    service = CompetencyService(db)
    try:
        return await service.archive(competency_id)
    except ValueError as e:
        _raise(str(e))


@router.post("/{competency_id}/unarchive", response_model=CompetencyRead)
async def unarchive_competency(
    competency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head")),
):
    service = CompetencyService(db)
    try:
        return await service.unarchive(competency_id)
    except ValueError as e:
        _raise(str(e))


@router.put("/{competency_id}/criteria", response_model=CompetencyRead)
async def upsert_criteria(
    competency_id: uuid.UUID,
    criteria: list[CriteriaUpsert],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head", "department_head")),
):
    service = CompetencyService(db)
    try:
        return await service.upsert_criteria(competency_id, criteria)
    except ValueError as e:
        _raise(str(e))
