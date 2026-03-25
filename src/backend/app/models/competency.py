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

from app.models.base import Base, TimestampMixin, UUIDMixin, pg_enum
from app.models.enums import CompetencyCategoryType


class CompetencyCategory(UUIDMixin, Base):
    __tablename__ = "competency_categories"

    name: Mapped[CompetencyCategoryType] = mapped_column(
        pg_enum(CompetencyCategoryType), unique=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text)

    competencies = relationship("Competency", back_populates="category")


class Competency(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "competencies"
    __table_args__ = (UniqueConstraint("category_id", "name", name="uq_competency_category_name"),)

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competency_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_common: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    category = relationship("CompetencyCategory", back_populates="competencies")
    departments = relationship(
        "Department", secondary="competency_departments", backref="competencies"
    )
    level_criteria = relationship(
        "CompetencyLevelCriteria", back_populates="competency", cascade="all, delete-orphan"
    )


class CompetencyDepartment(Base):
    __tablename__ = "competency_departments"

    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="CASCADE"),
        primary_key=True,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        primary_key=True,
    )


class ProficiencyLevel(UUIDMixin, Base):
    __tablename__ = "proficiency_levels"

    level: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (CheckConstraint("level >= 0 AND level <= 4", name="ck_level_range"),)


class CompetencyLevelCriteria(UUIDMixin, Base):
    __tablename__ = "competency_level_criteria"
    __table_args__ = (
        UniqueConstraint("competency_id", "level", name="uq_criteria_competency_level"),
        CheckConstraint("level >= 0 AND level <= 4", name="ck_criteria_level_range"),
    )

    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    criteria_description: Mapped[str] = mapped_column(Text, nullable=False)

    competency = relationship("Competency", back_populates="level_criteria")
