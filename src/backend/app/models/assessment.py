import uuid
from datetime import date, datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, pg_enum
from app.models.enums import (
    AssessmentStatus,
    AssessorType,
    CalibrationAction,
    CampaignScope,
    CampaignStatus,
)


class AssessmentCampaign(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "assessment_campaigns"
    __table_args__ = (CheckConstraint("end_date > start_date", name="ck_campaign_dates"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    scope: Mapped[CampaignScope] = mapped_column(
        pg_enum(CampaignScope),
        nullable=False,
        default=CampaignScope.DIVISION,
        server_default="division",
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL")
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        pg_enum(CampaignStatus),
        nullable=False,
        default=CampaignStatus.DRAFT,
        server_default="draft",
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    assessments = relationship(
        "Assessment", back_populates="campaign", cascade="all, delete-orphan"
    )


class Assessment(UUIDMixin, Base):
    __tablename__ = "assessments"
    __table_args__ = (
        UniqueConstraint("campaign_id", "assessee_id", "assessor_id", name="uq_assessment_triple"),
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assessor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assessor_type: Mapped[AssessorType] = mapped_column(pg_enum(AssessorType), nullable=False)
    status: Mapped[AssessmentStatus] = mapped_column(
        pg_enum(AssessmentStatus),
        nullable=False,
        default=AssessmentStatus.PENDING,
        server_default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    campaign = relationship("AssessmentCampaign", back_populates="assessments")
    assessee = relationship("User", foreign_keys=[assessee_id])
    assessor = relationship("User", foreign_keys=[assessor_id])
    scores = relationship(
        "AssessmentScore", back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentScore(UUIDMixin, Base):
    __tablename__ = "assessment_scores"
    __table_args__ = (
        UniqueConstraint("assessment_id", "competency_id", name="uq_score_assessment_competency"),
        CheckConstraint("score >= 0 AND score <= 4", name="ck_score_range"),
    )

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    is_draft: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    assessment = relationship("Assessment", back_populates="scores")
    competency = relationship("Competency")


class AggregatedScore(UUIDMixin, Base):
    __tablename__ = "aggregated_scores"
    __table_args__ = (
        UniqueConstraint("campaign_id", "user_id", "competency_id", name="uq_aggregated_score"),
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    final_score: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    self_score: Mapped[float | None] = mapped_column(Numeric(3, 2))
    peer_score: Mapped[float | None] = mapped_column(Numeric(3, 2))
    tl_score: Mapped[float | None] = mapped_column(Numeric(3, 2))
    dh_score: Mapped[float | None] = mapped_column(Numeric(3, 2))


class AssessmentWeight(UUIDMixin, Base):
    __tablename__ = "assessment_weights"

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_campaigns.id", ondelete="CASCADE"), unique=True
    )
    department_head_weight: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, server_default="0.35"
    )
    team_lead_weight: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, server_default="0.30"
    )
    self_weight: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, server_default="0.20"
    )
    peer_weight: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, server_default="0.15"
    )


class CalibrationFlag(UUIDMixin, Base):
    __tablename__ = "calibration_flags"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    max_spread: Mapped[int] = mapped_column(Integer, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")


class CalibrationAdjustment(UUIDMixin, Base):
    __tablename__ = "calibration_adjustments"

    flag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calibration_flags.id", ondelete="CASCADE"), nullable=False
    )
    adjusted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    action: Mapped[CalibrationAction] = mapped_column(pg_enum(CalibrationAction), nullable=False)
    original_score: Mapped[float | None] = mapped_column(Numeric(3, 2))
    adjusted_score: Mapped[float | None] = mapped_column(Numeric(3, 2))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )


class PeerSelection(UUIDMixin, Base):
    __tablename__ = "peer_selections"
    __table_args__ = (
        UniqueConstraint("campaign_id", "assessee_id", "peer_id", name="uq_peer_selection"),
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    peer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )
