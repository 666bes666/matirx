import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.development_plan import DevelopmentGoal, DevelopmentPlan, LearningResource
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.development_plan import (
    DevelopmentGoalCreate,
    DevelopmentGoalUpdate,
    DevelopmentPlanCreate,
    DevelopmentPlanUpdate,
    LearningResourceCreate,
)


class DevelopmentPlanService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_plans(self, current_user: User) -> list[DevelopmentPlan]:
        stmt = (
            select(DevelopmentPlan)
            .options(
                selectinload(DevelopmentPlan.user),
                selectinload(DevelopmentPlan.goals).selectinload(DevelopmentGoal.competency),
            )
            .where(DevelopmentPlan.is_archived.is_(False))
        )
        if current_user.role == UserRole.EMPLOYEE:
            stmt = stmt.where(DevelopmentPlan.user_id == current_user.id)
        elif current_user.role == UserRole.TEAM_LEAD:
            team_user_ids_r = await self.db.execute(
                select(User.id).where(User.team_id == current_user.team_id)
            )
            stmt = stmt.where(DevelopmentPlan.user_id.in_(team_user_ids_r.scalars().all()))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_plan(self, plan_id: uuid.UUID) -> DevelopmentPlan:
        result = await self.db.execute(
            select(DevelopmentPlan)
            .options(
                selectinload(DevelopmentPlan.user),
                selectinload(DevelopmentPlan.goals).selectinload(DevelopmentGoal.competency),
            )
            .where(DevelopmentPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if plan is None:
            raise ValueError("not_found")
        return plan

    async def create_plan(self, data: DevelopmentPlanCreate, creator: User) -> DevelopmentPlan:
        plan = DevelopmentPlan(user_id=data.user_id, created_by=creator.id)
        self.db.add(plan)
        await self.db.flush()
        return await self.get_plan(plan.id)

    async def update_plan(
        self, plan_id: uuid.UUID, data: DevelopmentPlanUpdate
    ) -> DevelopmentPlan:
        plan = await self.get_plan(plan_id)
        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(plan, k, v)
        await self.db.flush()
        return await self.get_plan(plan_id)

    async def archive_plan(self, plan_id: uuid.UUID) -> DevelopmentPlan:
        plan = await self.get_plan(plan_id)
        plan.is_archived = True
        await self.db.flush()
        return plan

    async def add_goal(self, plan_id: uuid.UUID, data: DevelopmentGoalCreate) -> DevelopmentGoal:
        await self.get_plan(plan_id)
        goal = DevelopmentGoal(
            plan_id=plan_id,
            competency_id=data.competency_id,
            current_level=data.current_level,
            target_level=data.target_level,
            deadline=data.deadline,
            is_mandatory=data.is_mandatory,
        )
        self.db.add(goal)
        await self.db.flush()
        result = await self.db.execute(
            select(DevelopmentGoal)
            .options(selectinload(DevelopmentGoal.competency))
            .where(DevelopmentGoal.id == goal.id)
        )
        return result.scalar_one()

    async def update_goal(
        self, goal_id: uuid.UUID, data: DevelopmentGoalUpdate
    ) -> DevelopmentGoal:
        result = await self.db.execute(
            select(DevelopmentGoal)
            .options(selectinload(DevelopmentGoal.competency))
            .where(DevelopmentGoal.id == goal_id)
        )
        goal = result.scalar_one_or_none()
        if goal is None:
            raise ValueError("goal_not_found")
        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(goal, k, v)
        await self.db.flush()
        return goal

    async def delete_goal(self, goal_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(DevelopmentGoal).where(DevelopmentGoal.id == goal_id)
        )
        goal = result.scalar_one_or_none()
        if goal is None:
            raise ValueError("goal_not_found")
        await self.db.delete(goal)
        await self.db.flush()

    async def list_resources(self, competency_id: uuid.UUID) -> list[LearningResource]:
        result = await self.db.execute(
            select(LearningResource)
            .where(LearningResource.competency_id == competency_id)
            .order_by(LearningResource.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_resource(
        self, competency_id: uuid.UUID, data: LearningResourceCreate
    ) -> LearningResource:
        resource = LearningResource(
            competency_id=competency_id,
            title=data.title,
            url=data.url,
            resource_type=data.resource_type,
            target_level=data.target_level,
            description=data.description,
        )
        self.db.add(resource)
        await self.db.flush()
        return resource

    async def delete_resource(self, resource_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(LearningResource).where(LearningResource.id == resource_id)
        )
        resource = result.scalar_one_or_none()
        if resource is None:
            raise ValueError("resource_not_found")
        await self.db.delete(resource)
        await self.db.flush()
