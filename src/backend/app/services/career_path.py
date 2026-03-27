import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment import AggregatedScore
from app.models.career_path import CareerPath, CareerPathRequirement
from app.schemas.career_path import CareerPathCreate, CareerPathRequirementInput


class CareerPathService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_paths(self) -> list[CareerPath]:
        result = await self.db.execute(
            select(CareerPath)
            .options(
                selectinload(CareerPath.from_department),
                selectinload(CareerPath.to_department),
                selectinload(CareerPath.requirements).selectinload(CareerPathRequirement.competency),
            )
            .where(CareerPath.is_active.is_(True))
            .order_by(CareerPath.created_at)
        )
        return list(result.scalars().all())

    async def get_path(self, path_id: uuid.UUID) -> CareerPath:
        result = await self.db.execute(
            select(CareerPath)
            .options(
                selectinload(CareerPath.from_department),
                selectinload(CareerPath.to_department),
                selectinload(CareerPath.requirements).selectinload(CareerPathRequirement.competency),
            )
            .where(CareerPath.id == path_id)
        )
        path = result.scalar_one_or_none()
        if path is None:
            raise ValueError("not_found")
        return path

    async def create_path(self, data: CareerPathCreate) -> CareerPath:
        existing = await self.db.execute(
            select(CareerPath).where(
                CareerPath.from_department_id == data.from_department_id,
                CareerPath.to_department_id == data.to_department_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("already_exists")
        path = CareerPath(
            from_department_id=data.from_department_id,
            to_department_id=data.to_department_id,
        )
        self.db.add(path)
        await self.db.flush()
        return await self.get_path(path.id)

    async def delete_path(self, path_id: uuid.UUID) -> None:
        path = await self.get_path(path_id)
        await self.db.delete(path)
        await self.db.flush()

    async def set_requirements(
        self, path_id: uuid.UUID, requirements: list[CareerPathRequirementInput]
    ) -> CareerPath:
        path = await self.get_path(path_id)
        await self.db.execute(
            delete(CareerPathRequirement).where(
                CareerPathRequirement.career_path_id == path_id
            )
        )
        for req in requirements:
            self.db.add(
                CareerPathRequirement(
                    career_path_id=path_id,
                    competency_id=req.competency_id,
                    required_level=req.required_level,
                    is_mandatory=req.is_mandatory,
                )
            )
        await self.db.flush()
        await self.db.refresh(path, ["requirements"])
        for req_obj in path.requirements:
            await self.db.refresh(req_obj, ["competency"])
        return path

    async def get_readiness(
        self, path_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict:
        path = await self.get_path(path_id)

        comp_ids = [r.competency_id for r in path.requirements]
        scores: dict[uuid.UUID, float] = {}
        if comp_ids:
            agg_result = await self.db.execute(
                select(AggregatedScore)
                .where(
                    AggregatedScore.user_id == user_id,
                    AggregatedScore.competency_id.in_(comp_ids),
                )
                .order_by(AggregatedScore.campaign_id.desc())
            )
            for agg in agg_result.scalars().all():
                if agg.competency_id not in scores:
                    scores[agg.competency_id] = float(agg.final_score)

        items = []
        mandatory_met_count = 0
        mandatory_total = 0
        desirable_met_count = 0
        desirable_total = 0

        for req in path.requirements:
            current = scores.get(req.competency_id)
            gap = None
            is_met = False
            if current is not None:
                gap = req.required_level - current
                is_met = current >= req.required_level

            if req.is_mandatory:
                mandatory_total += 1
                if is_met:
                    mandatory_met_count += 1
            else:
                desirable_total += 1
                if is_met:
                    desirable_met_count += 1

            items.append({
                "competency_id": req.competency_id,
                "competency_name": req.competency.name,
                "required_level": req.required_level,
                "is_mandatory": req.is_mandatory,
                "current_score": current,
                "gap": gap,
                "is_met": is_met,
            })

        total = len(path.requirements)
        met = sum(1 for it in items if it["is_met"])
        readiness_pct = round(met / total * 100, 1) if total > 0 else 0.0
        mandatory_met = mandatory_total == 0 or mandatory_met_count == mandatory_total
        desirable_pct = (
            desirable_met_count / desirable_total * 100
            if desirable_total > 0 else 100.0
        )
        is_ready = mandatory_met and desirable_pct >= 90.0

        return {
            "career_path_id": path_id,
            "user_id": user_id,
            "is_ready": is_ready,
            "readiness_pct": readiness_pct,
            "mandatory_met": mandatory_met,
            "items": items,
        }

    async def list_paths_for_department(self, department_id: uuid.UUID) -> list[CareerPath]:
        result = await self.db.execute(
            select(CareerPath)
            .options(
                selectinload(CareerPath.from_department),
                selectinload(CareerPath.to_department),
                selectinload(CareerPath.requirements).selectinload(CareerPathRequirement.competency),
            )
            .where(
                CareerPath.from_department_id == department_id,
                CareerPath.is_active.is_(True),
            )
        )
        return list(result.scalars().all())
