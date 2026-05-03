"""
backend/app/models/competition.py

CompetitionVote — tracks winner and runner-up votes for Competition quests.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class CompetitionVote(Base):
    __tablename__ = "competition_votes"
    __table_args__ = (
        UniqueConstraint("instance_id", "voter_id", name="uq_competition_vote"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quest_instances.id", ondelete="CASCADE"), nullable=False)
    voter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    winner_vote: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    runner_up_vote: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    instance: Mapped["QuestInstance"] = relationship("QuestInstance", back_populates="competition_votes")
    voter: Mapped["User"] = relationship("User", foreign_keys=[voter_id])
    winner_candidate: Mapped["User | None"] = relationship("User", foreign_keys=[winner_vote])
    runner_up_candidate: Mapped["User | None"] = relationship("User", foreign_keys=[runner_up_vote])


from app.models.quest import QuestInstance  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
