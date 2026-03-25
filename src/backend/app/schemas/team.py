import uuid

from pydantic import BaseModel


class TeamCreate(BaseModel):
    name: str
    description: str | None = None


class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class TeamRead(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID
    name: str
    description: str | None
    model_config = {"from_attributes": True}
