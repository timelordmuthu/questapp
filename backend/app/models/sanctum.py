"""
backend/app/models/sanctum.py
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Sanctum(Base):
    __tablename__ = "sanctums"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_sanctum_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="sanctum")
    quest_templates: Mapped[list["QuestTemplate"]] = relationship("QuestTemplate", back_populates="sanctum")


from app.models.user import User  # noqa: E402, F401
from app.models.quest import QuestTemplate  # noqa: E402, F401
