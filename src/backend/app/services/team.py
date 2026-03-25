import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate
from app.services.department import DepartmentService


class TeamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_dept(self, dept_id: uuid.UUID) -> list[Team]:
        result = await self.db.execute(
            select(Team).where(Team.department_id == dept_id).order_by(Team.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, team_id: uuid.UUID) -> Team:
        result = await self.db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()
        if team is None:
            raise ValueError("not_found")
        return team

    async def create(self, dept_id: uuid.UUID, data: TeamCreate) -> Team:
        dept_service = DepartmentService(self.db)
        await dept_service.get_by_id(dept_id)
        existing = await self.db.execute(
            select(Team).where(Team.department_id == dept_id, Team.name == data.name)
        )
        if existing.scalar_one_or_none():
            raise ValueError("name_taken")
        team = Team(
            department_id=dept_id,
            name=data.name,
            description=data.description,
        )
        self.db.add(team)
        await self.db.flush()
        await self.db.refresh(team)
        return team

    async def update(self, team_id: uuid.UUID, data: TeamUpdate) -> Team:
        team = await self.get_by_id(team_id)
        if data.name is not None and data.name != team.name:
            existing = await self.db.execute(
                select(Team).where(
                    Team.department_id == team.department_id, Team.name == data.name
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("name_taken")
            team.name = data.name
        if data.description is not None:
            team.description = data.description
        await self.db.flush()
        await self.db.refresh(team)
        return team

    async def delete(self, team_id: uuid.UUID) -> None:
        team = await self.get_by_id(team_id)
        count_result = await self.db.execute(
            select(func.count()).select_from(User).where(User.team_id == team_id)
        )
        if count_result.scalar_one() > 0:
            raise ValueError("team_not_empty")
        await self.db.delete(team)
        await self.db.flush()
