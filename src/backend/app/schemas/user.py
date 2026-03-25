import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    patronymic: str | None = None
    position: str | None = None
    role: UserRole = UserRole.EMPLOYEE
    department_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    telegram_username: str | None = None
    hire_date: date | None = None


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    patronymic: str | None = None
    position: str | None = None
    role: UserRole | None = None
    department_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    telegram_username: str | None = None
    hire_date: date | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    patronymic: str | None
    position: str | None
    role: UserRole
    department_id: uuid.UUID | None
    team_id: uuid.UUID | None
    telegram_username: str | None
    hire_date: date | None
    is_active: bool
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
