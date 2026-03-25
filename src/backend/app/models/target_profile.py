import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class TargetProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "target_profiles"
    __table_args__ = (
        UniqueConstraint("department_id", "position", name="uq_profile_dept_position"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    department = relationship("Department")
    competencies = relationship(
        "TargetProfileCompetency", back_populates="target_profile", cascade="all, delete-orphan"
    )


class TargetProfileCompetency(UUIDMixin, Base):
    __tablename__ = "target_profile_competencies"
    __table_args__ = (
        UniqueConstraint("target_profile_id", "competency_id", name="uq_profile_competency"),
        CheckConstraint(
            "required_level >= 0 AND required_level <= 4", name="ck_required_level_range"
        ),
    )

    target_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("target_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    target_profile = relationship("TargetProfile", back_populates="competencies")
    competency = relationship("Competency")
