import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import GoalStatus, PlanApproval, PlanStatus, ResourceType


class CompetencyBrief(BaseModel):
    id: uuid.UUID
    name: str
    model_config = {"from_attributes": True}


class LearningResourceCreate(BaseModel):
    title: str
    url: str | None = None
    resource_type: ResourceType = ResourceType.OTHER
    target_level: int | None = None
    description: str | None = None


class LearningResourceRead(BaseModel):
    id: uuid.UUID
    competency_id: uuid.UUID
    title: str
    url: str | None
    resource_type: ResourceType
    target_level: int | None
    description: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class DevelopmentGoalCreate(BaseModel):
    competency_id: uuid.UUID
    current_level: int
    target_level: int
    deadline: date | None = None
    is_mandatory: bool = False


class DevelopmentGoalUpdate(BaseModel):
    status: GoalStatus | None = None
    deadline: date | None = None
    target_level: int | None = None


class DevelopmentGoalRead(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    competency_id: uuid.UUID
    competency: CompetencyBrief
    current_level: int
    target_level: int
    status: GoalStatus
    deadline: date | None
    is_mandatory: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class DevelopmentPlanCreate(BaseModel):
    user_id: uuid.UUID


class DevelopmentPlanUpdate(BaseModel):
    status: PlanStatus | None = None
    approval: PlanApproval | None = None


class UserBrief(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    model_config = {"from_attributes": True}


class DevelopmentPlanRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user: UserBrief
    created_by: uuid.UUID
    status: PlanStatus
    approval: PlanApproval
    is_archived: bool
    goals: list[DevelopmentGoalRead] = []
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
