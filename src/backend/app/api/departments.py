import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import check_department_access, get_current_user, require_roles
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.schemas.team import TeamCreate, TeamRead, TeamUpdate
from app.services.department import DepartmentService
from app.services.team import TeamService

router = APIRouter(prefix="/departments", tags=["departments"])

ERROR_MAP = {
    "not_found": (status.HTTP_404_NOT_FOUND, "Не найдено"),
    "name_taken": (status.HTTP_409_CONFLICT, "Имя уже занято"),
    "protected": (status.HTTP_403_FORBIDDEN, "Предустановленные отделы нельзя удалять"),
    "team_not_empty": (status.HTTP_409_CONFLICT, "В команде есть сотрудники"),
}


def _raise(code: str) -> None:
    status_code, detail = ERROR_MAP.get(code, (400, code))
    raise HTTPException(status_code=status_code, detail=detail)


@router.get("", response_model=list[DepartmentRead])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = DepartmentService(db)
    depts = await service.list_all()
    return depts


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head")),
):
    service = DepartmentService(db)
    try:
        dept = await service.create(data)
    except ValueError as e:
        _raise(str(e))
    return dept


@router.get("/{dept_id}", response_model=DepartmentRead)
async def get_department(
    dept_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = DepartmentService(db)
    try:
        dept = await service.get_by_id(dept_id)
    except ValueError as e:
        _raise(str(e))
    return dept


@router.patch("/{dept_id}", response_model=DepartmentRead)
async def update_department(
    dept_id: uuid.UUID,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "head")),
):
    service = DepartmentService(db)
    try:
        dept = await service.update(dept_id, data)
    except ValueError as e:
        _raise(str(e))
    return dept


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    dept_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    service = DepartmentService(db)
    try:
        await service.delete(dept_id)
    except ValueError as e:
        _raise(str(e))


@router.get("/{dept_id}/teams", response_model=list[TeamRead])
async def list_teams(
    dept_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = TeamService(db)
    return await service.list_by_dept(dept_id)


@router.post(
    "/{dept_id}/teams",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_team(
    dept_id: uuid.UUID,
    data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "head", "department_head")),
):
    check_department_access(current_user, dept_id)
    service = TeamService(db)
    try:
        team = await service.create(dept_id, data)
    except ValueError as e:
        _raise(str(e))
    return team


@router.get("/{dept_id}/teams/{team_id}", response_model=TeamRead)
async def get_team(
    dept_id: uuid.UUID,
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = TeamService(db)
    try:
        team = await service.get_by_id(team_id)
    except ValueError as e:
        _raise(str(e))
    return team


@router.patch("/{dept_id}/teams/{team_id}", response_model=TeamRead)
async def update_team(
    dept_id: uuid.UUID,
    team_id: uuid.UUID,
    data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "head", "department_head")),
):
    check_department_access(current_user, dept_id)
    service = TeamService(db)
    try:
        team = await service.update(team_id, data)
    except ValueError as e:
        _raise(str(e))
    return team


@router.delete("/{dept_id}/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    dept_id: uuid.UUID,
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    service = TeamService(db)
    try:
        await service.delete(team_id)
    except ValueError as e:
        _raise(str(e))
