import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, pg_enum
from app.models.enums import ProposalStatus, ResourceAction


class CompetencyProposal(UUIDMixin, Base):
    __tablename__ = "competency_proposals"

    proposed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competency_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[ProposalStatus] = mapped_column(
        pg_enum(ProposalStatus),
        nullable=False,
        default=ProposalStatus.PENDING,
        server_default="pending",
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    review_comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )

    proposer = relationship("User", foreign_keys=[proposed_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class ResourceProposal(UUIDMixin, Base):
    __tablename__ = "resource_proposals"

    proposed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_resources.id", ondelete="SET NULL")
    )
    action: Mapped[ResourceAction] = mapped_column(pg_enum(ResourceAction), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    url: Mapped[str | None] = mapped_column(String(2000))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProposalStatus] = mapped_column(
        pg_enum(ProposalStatus),
        nullable=False,
        default=ProposalStatus.PENDING,
        server_default="pending",
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default="now()", nullable=False
    )

    proposer = relationship("User", foreign_keys=[proposed_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
