"""
backend/app/models/economy.py

PointTransaction, XpTransaction, Trade, DailyTradeCap, SeasonalPoints.

IMPORTANT: PointTransaction and XpTransaction are append-only audit ledgers.
Never UPDATE or DELETE rows from these tables.
"""

import uuid
import enum
from datetime import datetime, date

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class TransactionTypeEnum(str, enum.Enum):
    quest_reward = "quest_reward"
    competition_reward = "competition_reward"
    trade_sent = "trade_sent"
    trade_received = "trade_received"
    trade_tax = "trade_tax"


class TradeStatusEnum(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class PointTransaction(Base):
    """Append-only ledger for all point movements."""
    __tablename__ = "point_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # positive = credit, negative = debit
    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)  # snapshot for audit
    transaction_type: Mapped[TransactionTypeEnum] = mapped_column(Enum(TransactionTypeEnum, name="transaction_type_enum"), nullable=False)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)   # quest_instance_id or trade_id
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)               # "quest_instance" | "trade"
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship("User")


class XpTransaction(Base):
    """Append-only ledger for all XP movements."""
    __tablename__ = "xp_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship("User")


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    guild_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)
    amount_sent: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_received: Mapped[int] = mapped_column(Integer, nullable=False)  # floor(sent * 0.90)
    tax_amount: Mapped[int] = mapped_column(Integer, nullable=False)       # max(1, floor(sent * 0.10))
    status: Mapped[TradeStatusEnum] = mapped_column(Enum(TradeStatusEnum, name="trade_status_enum"), nullable=False, default=TradeStatusEnum.confirmed)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship("User", foreign_keys=[receiver_id])


class DailyTradeCap(Base):
    """Running tally of points sent per user per day (UTC date)."""
    __tablename__ = "daily_trade_caps"
    __table_args__ = (
        UniqueConstraint("user_id", "trade_date", name="uq_daily_trade_cap"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship("User")


class SeasonalPoints(Base):
    """
    Incremental monthly leaderboard cache (AD-02).
    Upserted on every point-earning event for O(1) leaderboard reads.
    """
    __tablename__ = "seasonal_points"
    __table_args__ = (
        UniqueConstraint("user_id", "guild_id", "season_year", "season_month", name="uq_seasonal_points"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    guild_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)
    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    season_month: Mapped[int] = mapped_column(Integer, nullable=False)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User")


from app.models.user import User  # noqa: E402, F401
