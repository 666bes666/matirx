import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class CareerPath(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "career_paths"
    __table_args__ = (
        UniqueConstraint("from_department_id", "to_department_id", name="uq_career_path"),
    )

    from_department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    to_department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    from_department = relationship("Department", foreign_keys=[from_department_id])
    to_department = relationship("Department", foreign_keys=[to_department_id])
    requirements = relationship(
        "CareerPathRequirement", back_populates="career_path", cascade="all, delete-orphan"
    )


class CareerPathRequirement(UUIDMixin, Base):
    __tablename__ = "career_path_requirements"
    __table_args__ = (
        UniqueConstraint("career_path_id", "competency_id", name="uq_career_path_competency"),
        CheckConstraint(
            "required_level >= 0 AND required_level <= 4", name="ck_career_req_level_range"
        ),
    )

    career_path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_paths.id", ondelete="CASCADE"), nullable=False
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    career_path = relationship("CareerPath", back_populates="requirements")
    competency = relationship("Competency")
