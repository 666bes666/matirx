import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import CompetencyCategoryType


class CompetencyCategoryRead(BaseModel):
    id: uuid.UUID
    name: CompetencyCategoryType
    description: str | None

    model_config = {"from_attributes": True}


class CriteriaRead(BaseModel):
    level: int
    criteria_description: str

    model_config = {"from_attributes": True}


class CriteriaUpsert(BaseModel):
    level: int
    criteria_description: str


class DepartmentBrief(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class CompetencyCreate(BaseModel):
    category_id: uuid.UUID
    name: str
    description: str | None = None
    is_common: bool = False
    department_ids: list[uuid.UUID] = []


class CompetencyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_common: bool | None = None
    category_id: uuid.UUID | None = None
    department_ids: list[uuid.UUID] | None = None


class CompetencyRead(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    category: CompetencyCategoryRead
    name: str
    description: str | None
    is_common: bool
    is_archived: bool
    departments: list[DepartmentBrief] = []
    level_criteria: list[CriteriaRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
