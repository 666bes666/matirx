import uuid

from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None
    sort_order: int = 0


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None


class TeamBrief(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    model_config = {"from_attributes": True}


class DepartmentRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    sort_order: int
    teams: list[TeamBrief] = []
    model_config = {"from_attributes": True}
