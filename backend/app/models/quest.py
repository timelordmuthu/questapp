"""
backend/app/models/quest.py

QuestTemplate, QuestInstance, QuestCompletion, SideQuest, SideQuestCompletion,
AddonQuest, AddonQuestCompletion
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
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

import enum


class QuestTypeEnum(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    occasional = "occasional"
    competition = "competition"
    group = "group"


class QuestCategoryEnum(str, enum.Enum):
    fitness = "fitness"
    study = "study"
    creative = "creative"
    social = "social"
    wellness = "wellness"
    other = "other"


class QuestStatusEnum(str, enum.Enum):
    pending_approval = "pending_approval"
    active = "active"
    upcoming = "upcoming"
    completed = "completed"
    cancelled = "cancelled"
    archived = "archived"


class CompletionStatusEnum(str, enum.Enum):
    pending = "pending"
    done = "done"
    missed = "missed"


class QuestTemplate(Base):
    __tablename__ = "quest_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Parent context — one of guild_id or sanctum_id must be set
    guild_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("guilds.id", ondelete="CASCADE"), nullable=True)
    sanctum_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sanctums.id", ondelete="CASCADE"), nullable=True)
    proposed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Core fields
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quest_type: Mapped[QuestTypeEnum] = mapped_column(Enum(QuestTypeEnum, name="quest_type_enum"), nullable=False)
    category: Mapped[QuestCategoryEnum] = mapped_column(Enum(QuestCategoryEnum, name="quest_category_enum"), nullable=False)
    category_custom_label: Mapped[str | None] = mapped_column(String(30), nullable=True)
    point_worth: Mapped[int] = mapped_column(Integer, nullable=False)
    xp_worth: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timing
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Competition-specific
    winner_point_reward: Mapped[int | None] = mapped_column(Integer, nullable=True)
    runner_up_point_reward: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Group-specific
    has_collective_deadline: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    collective_deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    status: Mapped[QuestStatusEnum] = mapped_column(Enum(QuestStatusEnum, name="quest_status_enum"), nullable=False, default=QuestStatusEnum.pending_approval)

    # Meta
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    guild: Mapped["Guild | None"] = relationship("Guild", back_populates="quest_templates")
    sanctum: Mapped["Sanctum | None"] = relationship("Sanctum", back_populates="quest_templates")
    proposer: Mapped["User"] = relationship("User", foreign_keys=[proposed_by])
    instances: Mapped[list["QuestInstance"]] = relationship("QuestInstance", back_populates="template", cascade="all, delete-orphan")
    side_quests: Mapped[list["SideQuest"]] = relationship("SideQuest", back_populates="parent_template", cascade="all, delete-orphan")
    addon_quests: Mapped[list["AddonQuest"]] = relationship("AddonQuest", back_populates="parent_template", cascade="all, delete-orphan")
    proposals: Mapped[list["QuestProposal"]] = relationship("QuestProposal", back_populates="template")


class QuestInstance(Base):
    """
    One row per time window of a recurring quest.
    Daily quests: one row per calendar day.
    Weekly quests: one row per Sun-Sat week.
    Occasional/competition/group: one row per activation.
    """
    __tablename__ = "quest_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quest_templates.id", ondelete="CASCADE"), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[QuestStatusEnum] = mapped_column(Enum(QuestStatusEnum, name="quest_status_enum"), nullable=False, default=QuestStatusEnum.active)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    template: Mapped["QuestTemplate"] = relationship("QuestTemplate", back_populates="instances")
    completions: Mapped[list["QuestCompletion"]] = relationship("QuestCompletion", back_populates="instance", cascade="all, delete-orphan")
    competition_votes: Mapped[list["CompetitionVote"]] = relationship("CompetitionVote", back_populates="instance", cascade="all, delete-orphan")


class QuestCompletion(Base):
    """One row per (instance_id, user_id) — tracks done/missed per member."""
    __tablename__ = "quest_completions"
    __table_args__ = (
        UniqueConstraint("instance_id", "user_id", name="uq_completion"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quest_instances.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[CompletionStatusEnum] = mapped_column(Enum(CompletionStatusEnum, name="completion_status_enum"), nullable=False, default=CompletionStatusEnum.pending)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    streak_multiplier_applied: Mapped[float | None] = mapped_column(nullable=True)

    # Wall of Glory
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pin_order: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1, 2, or 3

    instance: Mapped["QuestInstance"] = relationship("QuestInstance", back_populates="completions")
    user: Mapped["User"] = relationship("User")


class SideQuest(Base):
    __tablename__ = "side_quests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quest_templates.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    point_worth: Mapped[int] = mapped_column(Integer, nullable=False)
    xp_worth: Mapped[int] = mapped_column(Integer, nullable=False)
    unlock_hour_offset: Mapped[int] = mapped_column(Integer, nullable=False)  # hours after parent start
    unlocks_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="locked")  # locked / active / expired
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    parent_template: Mapped["QuestTemplate"] = relationship("QuestTemplate", back_populates="side_quests")
    completions: Mapped[list["SideQuestCompletion"]] = relationship("SideQuestCompletion", back_populates="side_quest", cascade="all, delete-orphan")


class SideQuestCompletion(Base):
    __tablename__ = "side_quest_completions"
    __table_args__ = (
        UniqueConstraint("side_quest_id", "user_id", name="uq_sq_completion"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    side_quest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("side_quests.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    side_quest: Mapped["SideQuest"] = relationship("SideQuest", back_populates="completions")
    user: Mapped["User"] = relationship("User")


class AddonQuest(Base):
    __tablename__ = "addon_quests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quest_templates.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    point_worth: Mapped[int] = mapped_column(Integer, nullable=False)
    xp_worth: Mapped[int] = mapped_column(Integer, nullable=False)
    addon_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="locked")  # locked / active / expired
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    parent_template: Mapped["QuestTemplate"] = relationship("QuestTemplate", back_populates="addon_quests")
    completions: Mapped[list["AddonQuestCompletion"]] = relationship("AddonQuestCompletion", back_populates="addon_quest", cascade="all, delete-orphan")


class AddonQuestCompletion(Base):
    __tablename__ = "addon_quest_completions"
    __table_args__ = (
        UniqueConstraint("addon_quest_id", "user_id", name="uq_aq_completion"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    addon_quest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("addon_quests.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    addon_quest: Mapped["AddonQuest"] = relationship("AddonQuest", back_populates="completions")
    user: Mapped["User"] = relationship("User")


# Deferred imports to avoid circular references
from app.models.guild import Guild  # noqa: E402, F401
from app.models.sanctum import Sanctum  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
from app.models.proposal import QuestProposal  # noqa: E402, F401
from app.models.competition import CompetitionVote  # noqa: E402, F401
