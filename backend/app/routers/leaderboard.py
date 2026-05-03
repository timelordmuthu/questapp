"""
backend/app/routers/leaderboard.py
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.economy import SeasonalPoints
from app.models.guild import Guild, GuildMember
from app.models.user import User
from app.utils.xp import get_level_title

router = APIRouter()


@router.get("/guilds/{guild_id}")
async def get_leaderboard(
    guild_id: uuid.UUID,
    type: str = Query("all_time", enum=["all_time", "seasonal"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify membership
    result = await db.execute(
        select(GuildMember).where(
            GuildMember.guild_id == guild_id,
            GuildMember.user_id == current_user.id,
            GuildMember.is_active == True,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this Guild.")

    result = await db.execute(select(Guild).where(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    if not guild:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guild not found.")

    now = datetime.now(timezone.utc)
    season_year = now.year
    season_month = now.month

    if type == "all_time":
        result = await db.execute(
            select(User, GuildMember)
            .join(GuildMember, User.id == GuildMember.user_id)
            .where(GuildMember.guild_id == guild_id, GuildMember.is_active == True)
            .order_by(User.total_points.desc())
        )
        rows = result.fetchall()
        entries = []
        for rank, (user, _) in enumerate(rows, start=1):
            entries.append({
                "rank": rank,
                "user_id": user.id,
                "player_name": user.player_name,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "current_level": user.current_level,
                "level_title": get_level_title(user.current_level),
                "points": user.total_points,
                "is_current_user": str(user.id) == str(current_user.id),
            })
    else:
        result = await db.execute(
            select(SeasonalPoints, User)
            .join(User, SeasonalPoints.user_id == User.id)
            .join(GuildMember, (GuildMember.guild_id == guild_id) & (GuildMember.user_id == User.id))
            .where(
                SeasonalPoints.guild_id == guild_id,
                SeasonalPoints.season_year == season_year,
                SeasonalPoints.season_month == season_month,
                GuildMember.is_active == True,
            )
            .order_by(SeasonalPoints.points_earned.desc())
        )
        rows = result.fetchall()
        entries = []
        for rank, (sp, user) in enumerate(rows, start=1):
            entries.append({
                "rank": rank,
                "user_id": user.id,
                "player_name": user.player_name,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "current_level": user.current_level,
                "level_title": get_level_title(user.current_level),
                "points": sp.points_earned,
                "is_current_user": str(user.id) == str(current_user.id),
            })

    return {
        "guild_id": guild_id,
        "guild_name": guild.name,
        "type": type,
        "season_year": season_year if type == "seasonal" else None,
        "season_month": season_month if type == "seasonal" else None,
        "entries": entries,
    }
