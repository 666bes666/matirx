import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, validate_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

_EMPLOYEE_EDITABLE = {"first_name", "last_name", "patronymic", "telegram_username"}
_READ_ONLY_ROLES = {UserRole.HEAD, UserRole.HR}


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(
        self,
        current_user: User,
        search: str | None = None,
        department_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> list[User]:
        query = select(User).options(
            selectinload(User.department),
            selectinload(User.team),
        )

        if current_user.role == UserRole.TEAM_LEAD:
            query = query.where(User.team_id == current_user.team_id)
        elif current_user.role == UserRole.EMPLOYEE:
            query = query.where(User.id == current_user.id)

        if department_id is not None:
            query = query.where(User.department_id == department_id)
        if team_id is not None:
            query = query.where(User.team_id == team_id)
        if role is not None:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )

        query = query.order_by(User.last_name, User.first_name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.department), selectinload(User.team))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("not_found")
        return user

    async def create(self, data: UserCreate) -> User:
        existing = await self.db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise ValueError("email_taken")

        if not validate_password(data.password):
            raise ValueError("weak_password")

        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            patronymic=data.patronymic,
            position=data.position,
            role=data.role,
            department_id=data.department_id,
            team_id=data.team_id,
            telegram_username=data.telegram_username,
            hire_date=data.hire_date,
            is_active=False,
        )
        self.db.add(user)
        await self.db.flush()
        return await self.get_by_id(user.id)

    async def update(
        self,
        user_id: uuid.UUID,
        data: UserUpdate,
        current_user: User,
    ) -> User:
        user = await self.get_by_id(user_id)

        if current_user.role == UserRole.EMPLOYEE:
            if current_user.id != user_id:
                raise ValueError("forbidden")
        elif current_user.role == UserRole.TEAM_LEAD:
            if current_user.team_id != user.team_id:
                raise ValueError("forbidden")
        elif current_user.role == UserRole.DEPARTMENT_HEAD:
            if current_user.department_id != user.department_id:
                raise ValueError("forbidden")
        elif current_user.role in _READ_ONLY_ROLES and not (
            data.is_active is not None and len(data.model_dump(exclude_unset=True)) == 1
        ):
            raise ValueError("forbidden")

        update_data = data.model_dump(exclude_unset=True)

        if current_user.role == UserRole.EMPLOYEE:
            update_data = {k: v for k, v in update_data.items() if k in _EMPLOYEE_EDITABLE}

        for key, value in update_data.items():
            setattr(user, key, value)

        await self.db.flush()
        return await self.get_by_id(user_id)

    async def activate(self, user_id: uuid.UUID) -> User:
        user = await self.get_by_id(user_id)
        user.is_active = True
        await self.db.flush()
        return await self.get_by_id(user_id)

    async def deactivate(self, user_id: uuid.UUID) -> User:
        user = await self.get_by_id(user_id)
        user.is_active = False
        await self.db.flush()
        return await self.get_by_id(user_id)
