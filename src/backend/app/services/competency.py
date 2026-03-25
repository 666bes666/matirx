import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.competency import (
    Competency,
    CompetencyCategory,
    CompetencyDepartment,
    CompetencyLevelCriteria,
)
from app.schemas.competency import CompetencyCreate, CompetencyUpdate, CriteriaUpsert


class CompetencyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_categories(self) -> list[CompetencyCategory]:
        result = await self.db.execute(select(CompetencyCategory))
        return list(result.scalars().all())

    async def list_competencies(
        self,
        category_id: uuid.UUID | None = None,
        department_id: uuid.UUID | None = None,
        is_common: bool | None = None,
        is_archived: bool | None = None,
        search: str | None = None,
    ) -> list[Competency]:
        query = select(Competency).options(
            selectinload(Competency.category),
            selectinload(Competency.departments),
            selectinload(Competency.level_criteria),
        )

        if category_id is not None:
            query = query.where(Competency.category_id == category_id)
        if is_common is not None:
            query = query.where(Competency.is_common == is_common)
        if is_archived is not None:
            query = query.where(Competency.is_archived == is_archived)
        else:
            query = query.where(Competency.is_archived.is_(False))
        if department_id is not None:
            query = query.join(
                CompetencyDepartment,
                CompetencyDepartment.competency_id == Competency.id,
            ).where(CompetencyDepartment.department_id == department_id)
        if search:
            query = query.where(Competency.name.ilike(f"%{search}%"))

        query = query.order_by(Competency.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, competency_id: uuid.UUID) -> Competency:
        result = await self.db.execute(
            select(Competency)
            .options(
                selectinload(Competency.category),
                selectinload(Competency.departments),
                selectinload(Competency.level_criteria),
            )
            .where(Competency.id == competency_id)
        )
        comp = result.scalar_one_or_none()
        if comp is None:
            raise ValueError("not_found")
        return comp

    async def create(self, data: CompetencyCreate) -> Competency:
        category = await self.db.get(CompetencyCategory, data.category_id)
        if category is None:
            raise ValueError("category_not_found")

        existing = await self.db.execute(
            select(Competency).where(
                Competency.category_id == data.category_id,
                Competency.name == data.name,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("name_taken")

        comp = Competency(
            category_id=data.category_id,
            name=data.name,
            description=data.description,
            is_common=data.is_common,
        )
        self.db.add(comp)
        await self.db.flush()

        for dept_id in data.department_ids:
            self.db.add(CompetencyDepartment(competency_id=comp.id, department_id=dept_id))
        await self.db.flush()

        return await self.get_by_id(comp.id)

    async def update(self, competency_id: uuid.UUID, data: CompetencyUpdate) -> Competency:
        comp = await self.get_by_id(competency_id)

        if data.name is not None and data.name != comp.name:
            category_id = data.category_id or comp.category_id
            existing = await self.db.execute(
                select(Competency).where(
                    Competency.category_id == category_id,
                    Competency.name == data.name,
                    Competency.id != competency_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("name_taken")
            comp.name = data.name

        if data.description is not None:
            comp.description = data.description
        if data.is_common is not None:
            comp.is_common = data.is_common
        if data.category_id is not None:
            comp.category_id = data.category_id

        if data.department_ids is not None:
            await self.db.execute(
                delete(CompetencyDepartment).where(
                    CompetencyDepartment.competency_id == competency_id
                )
            )
            for dept_id in data.department_ids:
                self.db.add(
                    CompetencyDepartment(competency_id=competency_id, department_id=dept_id)
                )

        await self.db.flush()
        return await self.get_by_id(competency_id)

    async def archive(self, competency_id: uuid.UUID) -> Competency:
        comp = await self.get_by_id(competency_id)
        comp.is_archived = True
        await self.db.flush()
        return await self.get_by_id(competency_id)

    async def unarchive(self, competency_id: uuid.UUID) -> Competency:
        comp = await self.get_by_id(competency_id)
        comp.is_archived = False
        await self.db.flush()
        return await self.get_by_id(competency_id)

    async def upsert_criteria(
        self, competency_id: uuid.UUID, criteria_list: list[CriteriaUpsert]
    ) -> Competency:
        await self.get_by_id(competency_id)

        for criteria in criteria_list:
            result = await self.db.execute(
                select(CompetencyLevelCriteria).where(
                    CompetencyLevelCriteria.competency_id == competency_id,
                    CompetencyLevelCriteria.level == criteria.level,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.criteria_description = criteria.criteria_description
            else:
                self.db.add(
                    CompetencyLevelCriteria(
                        competency_id=competency_id,
                        level=criteria.level,
                        criteria_description=criteria.criteria_description,
                    )
                )

        await self.db.flush()
        return await self.get_by_id(competency_id)
