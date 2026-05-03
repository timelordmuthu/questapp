"""
backend/app/models/proposal.py

QuestProposal, ProposalVote
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ProposalTypeEnum(str, enum.Enum):
    create = "create"
    edit = "edit"
    delete = "delete"


class ProposalStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class VoteEnum(str, enum.Enum):
    accept = "accept"
    decline = "decline"
    suggest_changes = "suggest_changes"


class QuestProposal(Base):
    __tablename__ = "quest_proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("quest_templates.id", ondelete="SET NULL"), nullable=True)
    proposed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    proposal_type: Mapped[ProposalTypeEnum] = mapped_column(Enum(ProposalTypeEnum, name="proposal_type_enum"), nullable=False)
    status: Mapped[ProposalStatusEnum] = mapped_column(Enum(ProposalStatusEnum, name="proposal_status_enum"), nullable=False, default=ProposalStatusEnum.pending)

    # Snapshot of proposed quest data (JSON)
    proposed_data: Mapped[str] = mapped_column(Text, nullable=False)
    # Suggest changes notes
    suggest_changes_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    voting_closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # proposed_at + 48h
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    guild: Mapped["Guild"] = relationship("Guild", back_populates="proposals")
    template: Mapped["QuestTemplate | None"] = relationship("QuestTemplate", back_populates="proposals")
    proposer: Mapped["User"] = relationship("User", foreign_keys=[proposed_by])
    votes: Mapped[list["ProposalVote"]] = relationship("ProposalVote", back_populates="proposal", cascade="all, delete-orphan")


class ProposalVote(Base):
    __tablename__ = "proposal_votes"
    __table_args__ = (
        UniqueConstraint("proposal_id", "user_id", name="uq_proposal_vote"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quest_proposals.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vote: Mapped[VoteEnum] = mapped_column(Enum(VoteEnum, name="vote_enum"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    proposal: Mapped["QuestProposal"] = relationship("QuestProposal", back_populates="votes")
    voter: Mapped["User"] = relationship("User")


from app.models.guild import Guild  # noqa: E402, F401
from app.models.quest import QuestTemplate  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
