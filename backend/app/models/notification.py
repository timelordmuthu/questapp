"""
backend/app/models/notification.py
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class NotificationCategoryEnum(str, enum.Enum):
    proposals_voting = "proposals_voting"
    deadline_reminders = "deadline_reminders"
    level_badge = "level_badge"
    trade_alerts = "trade_alerts"
    group_progress = "group_progress"
    guild_membership = "guild_membership"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[NotificationCategoryEnum] = mapped_column(Enum(NotificationCategoryEnum, name="notification_category_enum"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # created_at + 30 days
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notifications")


class NotificationSetting(Base):
    """Per-user notification category preferences."""
    __tablename__ = "notification_settings"
    __table_args__ = (UniqueConstraint("user_id", "category", name="uq_notif_setting"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[NotificationCategoryEnum] = mapped_column(Enum(NotificationCategoryEnum, name="notification_category_enum"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship("User")


from app.models.user import User  # noqa: E402, F401
