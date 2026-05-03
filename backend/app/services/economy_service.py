"""
backend/app/services/economy_service.py

Points and XP awarding, level-up detection, seasonal leaderboard upsert,
trade execution.
"""

import math
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.economy import (
    DailyTradeCap,
    PointTransaction,
    SeasonalPoints,
    Trade,
    TransactionTypeEnum,
    XpTransaction,
)
from app.models.user import User
from app.utils.xp import apply_xp, get_level_title, level_from_total_xp
from app.utils.trade import validate_trade


async def award_points_and_xp(
    user: User,
    points: int,
    xp: int,
    quest_type: str,
    reference_id: uuid.UUID,
    reference_type: str,
    description: str,
    guild_id: uuid.UUID | None,
    db: AsyncSession,
) -> dict:
    """
    Award points and XP to a user after quest completion.
    Returns dict with new totals and level_up flag.
    """
    # Apply streak multiplier to XP
    final_xp = apply_xp(xp, quest_type, user.daily_streak, user.weekly_streak)
    multiplier = final_xp / xp if xp > 0 else 1.0

    old_level = user.current_level
    new_points = user.total_points + points
    new_xp = user.total_xp + final_xp
    new_level = level_from_total_xp(new_xp)

    # Update user
    await db.execute(
        update(User).where(User.id == user.id).values(
            total_points=new_points,
            total_xp=new_xp,
            current_level=new_level,
        )
    )

    # Append-only point transaction
    db.add(PointTransaction(
        user_id=user.id,
        amount=points,
        balance_after=new_points,
        transaction_type=TransactionTypeEnum.quest_reward,
        reference_id=reference_id,
        reference_type=reference_type,
        description=description,
    ))

    # Append-only XP transaction
    db.add(XpTransaction(
        user_id=user.id,
        amount=final_xp,
        balance_after=new_xp,
        reference_id=reference_id,
        reference_type=reference_type,
        description=description,
    ))

    # Upsert seasonal leaderboard (AD-02)
    if guild_id and points > 0:
        now = datetime.now(timezone.utc)
        stmt = pg_insert(SeasonalPoints).values(
            user_id=user.id,
            guild_id=guild_id,
            season_year=now.year,
            season_month=now.month,
            points_earned=points,
        ).on_conflict_do_update(
            index_elements=["user_id", "guild_id", "season_year", "season_month"],
            set_={"points_earned": SeasonalPoints.points_earned + points},
        )
        await db.execute(stmt)

    return {
        "points_earned": points,
        "xp_earned": final_xp,
        "new_total_points": new_points,
        "new_total_xp": new_xp,
        "new_level": new_level,
        "level_up": new_level > old_level,
        "streak_multiplier": round(multiplier, 2),
    }


async def execute_trade(
    sender: User,
    receiver: User,
    guild_id: uuid.UUID,
    amount_sent: int,
    db: AsyncSession,
) -> Trade:
    """Execute a trade with tax. Validates before executing."""
    # Get daily sent total
    today = date.today()
    result = await db.execute(
        select(DailyTradeCap).where(
            DailyTradeCap.user_id == sender.id,
            DailyTradeCap.trade_date == today,
        )
    )
    cap_record = result.scalar_one_or_none()
    daily_sent = cap_record.total_sent if cap_record else 0

    validation = validate_trade(sender.total_points, amount_sent, daily_sent)
    if not validation["valid"]:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=validation["errors"])

    tax = validation["tax"]
    received = validation["received"]

    # Deduct from sender
    sender_new_points = sender.total_points - amount_sent
    await db.execute(update(User).where(User.id == sender.id).values(total_points=sender_new_points))

    # Credit receiver
    receiver_new_points = receiver.total_points + received
    await db.execute(update(User).where(User.id == receiver.id).values(total_points=receiver_new_points))

    # Append transactions
    trade = Trade(
        sender_id=sender.id,
        receiver_id=receiver.id,
        guild_id=guild_id,
        amount_sent=amount_sent,
        amount_received=received,
        tax_amount=tax,
    )
    db.add(trade)
    await db.flush()

    db.add(PointTransaction(
        user_id=sender.id,
        amount=-amount_sent,
        balance_after=sender_new_points,
        transaction_type=TransactionTypeEnum.trade_sent,
        reference_id=trade.id,
        reference_type="trade",
        description=f"Trade to {receiver.player_name}",
    ))
    db.add(PointTransaction(
        user_id=receiver.id,
        amount=received,
        balance_after=receiver_new_points,
        transaction_type=TransactionTypeEnum.trade_received,
        reference_id=trade.id,
        reference_type="trade",
        description=f"Trade from {sender.player_name}",
    ))

    # Update daily trade cap
    if cap_record:
        await db.execute(
            update(DailyTradeCap)
            .where(DailyTradeCap.id == cap_record.id)
            .values(total_sent=DailyTradeCap.total_sent + amount_sent)
        )
    else:
        db.add(DailyTradeCap(user_id=sender.id, trade_date=today, total_sent=amount_sent))

    return trade
