import uuid
from datetime import datetime

from pydantic import BaseModel


class DepartmentBrief(BaseModel):
    id: uuid.UUID
    name: str
    model_config = {"from_attributes": True}


class CompetencyBrief(BaseModel):
    id: uuid.UUID
    name: str
    model_config = {"from_attributes": True}


class CareerPathRequirementInput(BaseModel):
    competency_id: uuid.UUID
    required_level: int
    is_mandatory: bool = False


class CareerPathRequirementRead(BaseModel):
    id: uuid.UUID
    career_path_id: uuid.UUID
    competency_id: uuid.UUID
    competency: CompetencyBrief
    required_level: int
    is_mandatory: bool
    model_config = {"from_attributes": True}


class CareerPathCreate(BaseModel):
    from_department_id: uuid.UUID
    to_department_id: uuid.UUID


class CareerPathRead(BaseModel):
    id: uuid.UUID
    from_department_id: uuid.UUID
    to_department_id: uuid.UUID
    from_department: DepartmentBrief
    to_department: DepartmentBrief
    is_active: bool
    requirements: list[CareerPathRequirementRead] = []
    created_at: datetime
    model_config = {"from_attributes": True}


class ReadinessItem(BaseModel):
    competency_id: uuid.UUID
    competency_name: str
    required_level: int
    is_mandatory: bool
    current_score: float | None
    gap: float | None
    is_met: bool


class CareerReadinessRead(BaseModel):
    career_path_id: uuid.UUID
    user_id: uuid.UUID
    is_ready: bool
    readiness_pct: float
    mandatory_met: bool
    items: list[ReadinessItem]
