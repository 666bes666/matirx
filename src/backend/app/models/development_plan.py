import uuid
from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, pg_enum
from app.models.enums import GoalStatus, PlanApproval, PlanStatus, ResourceType


class DevelopmentPlan(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "development_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    status: Mapped[PlanStatus] = mapped_column(
        pg_enum(PlanStatus), nullable=False, default=PlanStatus.DRAFT, server_default="draft"
    )
    approval: Mapped[PlanApproval] = mapped_column(
        pg_enum(PlanApproval),
        nullable=False,
        default=PlanApproval.PENDING,
        server_default="pending",
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    user = relationship("User", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])
    goals = relationship("DevelopmentGoal", back_populates="plan", cascade="all, delete-orphan")


class DevelopmentGoal(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "development_goals"
    __table_args__ = (
        CheckConstraint("target_level > current_level", name="ck_goal_target_gt_current"),
        CheckConstraint("current_level >= 0 AND current_level <= 4", name="ck_goal_current_range"),
        CheckConstraint("target_level >= 0 AND target_level <= 4", name="ck_goal_target_range"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("development_plans.id", ondelete="CASCADE"), nullable=False
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    current_level: Mapped[int] = mapped_column(Integer, nullable=False)
    target_level: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[GoalStatus] = mapped_column(
        pg_enum(GoalStatus), nullable=False, default=GoalStatus.PLANNED, server_default="planned"
    )
    deadline: Mapped[date | None] = mapped_column(Date)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    plan = relationship("DevelopmentPlan", back_populates="goals")
    competency = relationship("Competency")
    resources = relationship("LearningResource", secondary="goal_resources", backref="goals")


class LearningResource(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "learning_resources"

    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2000))
    resource_type: Mapped[ResourceType] = mapped_column(
        pg_enum(ResourceType), nullable=False, default=ResourceType.OTHER, server_default="other"
    )
    target_level: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)

    competency = relationship("Competency")


class GoalResource(Base):
    __tablename__ = "goal_resources"

    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("development_goals.id", ondelete="CASCADE"),
        primary_key=True,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_resources.id", ondelete="CASCADE"),
        primary_key=True,
    )
