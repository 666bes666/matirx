import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.department import Department
from app.models.team import Team
from app.schemas.department import DepartmentCreate, DepartmentUpdate

PROTECTED_DEPARTMENTS = {
    "Первая линия",
    "Дежурная смена",
    "Бизнес-логика",
    "Вторая линия (SRE)",
    "Сопровождение Jenkins CDP",
}


class DepartmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[Department]:
        result = await self.db.execute(
            select(Department)
            .options(selectinload(Department.teams))
            .order_by(Department.sort_order)
        )
        return list(result.scalars().all())

    async def get_by_id(self, dept_id: uuid.UUID) -> Department:
        result = await self.db.execute(
            select(Department)
            .options(selectinload(Department.teams))
            .where(Department.id == dept_id)
        )
        dept = result.scalar_one_or_none()
        if dept is None:
            raise ValueError("not_found")
        return dept

    async def create(self, data: DepartmentCreate) -> Department:
        existing = await self.db.execute(
            select(Department).where(Department.name == data.name)
        )
        if existing.scalar_one_or_none():
            raise ValueError("name_taken")
        dept = Department(
            name=data.name,
            description=data.description,
            sort_order=data.sort_order,
        )
        self.db.add(dept)
        await self.db.flush()
        return await self.get_by_id(dept.id)

    async def update(self, dept_id: uuid.UUID, data: DepartmentUpdate) -> Department:
        dept = await self.get_by_id(dept_id)
        if data.name is not None and data.name != dept.name:
            existing = await self.db.execute(
                select(Department).where(Department.name == data.name)
            )
            if existing.scalar_one_or_none():
                raise ValueError("name_taken")
            dept.name = data.name
        if data.description is not None:
            dept.description = data.description
        if data.sort_order is not None:
            dept.sort_order = data.sort_order
        await self.db.flush()
        return await self.get_by_id(dept_id)

    async def delete(self, dept_id: uuid.UUID) -> None:
        dept = await self.get_by_id(dept_id)
        if dept.name in PROTECTED_DEPARTMENTS:
            raise ValueError("protected")
        count_result = await self.db.execute(
            select(func.count()).select_from(Team).where(Team.department_id == dept_id)
        )
        if count_result.scalar_one() > 0:
            raise ValueError("team_not_empty")
        await self.db.delete(dept)
        await self.db.flush()
