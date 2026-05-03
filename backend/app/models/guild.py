"""
backend/app/models/guild.py

Guild, GuildMember, GuildArchive
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Guild(Base):
    __tablename__ = "guilds"
    __table_args__ = (
        UniqueConstraint("sigil_code", name="uq_sigil_code"),
        CheckConstraint("max_points_per_quest > 0", name="chk_points_cap"),
        CheckConstraint("max_xp_per_quest > 0", name="chk_xp_cap"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sigil_code: Mapped[str] = mapped_column(String(20), nullable=False)
    guild_master_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Anti-exploitation caps
    max_points_per_quest: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    max_xp_per_quest: Mapped[int] = mapped_column(Integer, nullable=False, default=200)

    # Lifecycle
    is_dissolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dissolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Meta
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    guild_master: Mapped["User"] = relationship("User", foreign_keys=[guild_master_id])
    members: Mapped[list["GuildMember"]] = relationship("GuildMember", back_populates="guild", cascade="all, delete-orphan")
    quest_templates: Mapped[list["QuestTemplate"]] = relationship("QuestTemplate", back_populates="guild")
    proposals: Mapped[list["QuestProposal"]] = relationship("QuestProposal", back_populates="guild")
    archives: Mapped[list["GuildArchive"]] = relationship("GuildArchive", back_populates="guild", cascade="all, delete-orphan")


class GuildMember(Base):
    __tablename__ = "guild_members"
    __table_args__ = (
        UniqueConstraint("guild_id", "user_id", name="uq_guild_member"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="guild_memberships")


class GuildArchive(Base):
    """Stores dissolved guild quest history for 90 days."""
    __tablename__ = "guild_archives"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)
    guild_name: Mapped[str] = mapped_column(String(100), nullable=False)
    archive_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON snapshot
    dissolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    purge_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # dissolved_at + 90 days
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    guild: Mapped["Guild"] = relationship("Guild", back_populates="archives")


from app.models.user import User  # noqa: E402, F401
from app.models.quest import QuestTemplate  # noqa: E402, F401
from app.models.proposal import QuestProposal  # noqa: E402, F401
