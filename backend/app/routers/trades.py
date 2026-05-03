"""
backend/app/routers/trades.py
"""

import math
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.economy import DailyTradeCap
from app.models.guild import Guild, GuildMember
from app.models.user import User
from app.schemas.guild import TradeRequest, TradeValidateRequest, TradeValidateResponse
from app.services.badge_service import check_trade_badges
from app.services.economy_service import execute_trade
from app.services.notification_service import notify_badge_earned, notify_trade_received
from app.utils.trade import validate_trade

router = APIRouter()


@router.post("/validate", response_model=TradeValidateResponse)
async def validate_trade_request(
    data: TradeValidateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    result = await db.execute(
        select(DailyTradeCap).where(DailyTradeCap.user_id == current_user.id, DailyTradeCap.trade_date == today)
    )
    cap_record = result.scalar_one_or_none()
    daily_sent = cap_record.total_sent if cap_record else 0
    daily_cap = math.floor(current_user.total_points * 0.20)

    v = validate_trade(current_user.total_points, data.amount, daily_sent)
    return {
        "valid": v["valid"],
        "errors": v["errors"],
        "tax": v["tax"],
        "received": v["received"],
        "daily_cap": daily_cap,
        "daily_sent_today": daily_sent,
    }


@router.post("", status_code=201)
async def send_trade(
    data: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify both users are members of the specified guild
    result = await db.execute(
        select(GuildMember).where(
            GuildMember.guild_id == data.guild_id,
            GuildMember.user_id == current_user.id,
            GuildMember.is_active == True,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this Guild.")

    result = await db.execute(select(User).where(User.player_name == data.receiver_player_name))
    receiver = result.scalar_one_or_none()
    if not receiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receiver not found.")
    if str(receiver.id) == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot trade with yourself.")

    result = await db.execute(
        select(GuildMember).where(
            GuildMember.guild_id == data.guild_id,
            GuildMember.user_id == receiver.id,
            GuildMember.is_active == True,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receiver is not a member of this Guild.")

    trade = await execute_trade(current_user, receiver, data.guild_id, data.amount, db)

    # Notify receiver
    await notify_trade_received(receiver.id, current_user.player_name, trade.amount_received, db)

    # Badge checks
    badges = await check_trade_badges(current_user.id, db)
    for b in badges:
        await notify_badge_earned(current_user.id, b, db)

    return {
        "trade_id": str(trade.id),
        "amount_sent": trade.amount_sent,
        "amount_received": trade.amount_received,
        "tax": trade.tax_amount,
    }
