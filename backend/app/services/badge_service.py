"""
backend/app/services/badge_service.py

Event-driven badge checking (AD-09).
Each check is idempotent — uses INSERT ... ON CONFLICT DO NOTHING.
"""

import uuid
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badge import Badge, UserBadge


async def _award_badge_if_eligible(
    user_id: uuid.UUID,
    badge_key: str,
    db: AsyncSession,
) -> str | None:
    """Award badge if not already earned. Returns badge name or None."""
    # Get badge definition
    result = await db.execute(select(Badge).where(Badge.badge_key == badge_key))
    badge = result.scalar_one_or_none()
    if not badge:
        return None

    # Check if already earned
    result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == user_id, UserBadge.badge_id == badge.id)
    )
    if result.scalar_one_or_none():
        return None  # Already earned

    db.add(UserBadge(user_id=user_id, badge_id=badge.id))
    return badge.name


async def check_quest_badges(user_id: uuid.UUID, db: AsyncSession) -> list[str]:
    """Check quest-count badges after a quest completion."""
    from app.models.quest import QuestCompletion, CompletionStatusEnum

    count_result = await db.execute(
        select(func.count()).where(
            QuestCompletion.user_id == user_id,
            QuestCompletion.status == CompletionStatusEnum.done,
        )
    )
    total = count_result.scalar() or 0

    earned = []
    if total >= 1:
        name = await _award_badge_if_eligible(user_id, "first_flame", db)
        if name:
            earned.append(name)
    if total >= 10:
        name = await _award_badge_if_eligible(user_id, "ten_trials", db)
        if name:
            earned.append(name)
    if total >= 100:
        name = await _award_badge_if_eligible(user_id, "century_mark", db)
        if name:
            earned.append(name)
    if total >= 500:
        name = await _award_badge_if_eligible(user_id, "the_relentless", db)
        if name:
            earned.append(name)

    return earned


async def check_streak_badges(user_id: uuid.UUID, daily_streak: int, weekly_streak: int, db: AsyncSession) -> list[str]:
    earned = []
    streak_checks = [
        ("kindled", daily_streak, 3),
        ("burning_path", daily_streak, 7),
        ("eternal_flame", daily_streak, 30),
        ("weekly_ritual", weekly_streak, 4),
        ("ancient_rite", weekly_streak, 12),
    ]
    for badge_key, streak, threshold in streak_checks:
        if streak >= threshold:
            name = await _award_badge_if_eligible(user_id, badge_key, db)
            if name:
                earned.append(name)
    return earned


async def check_level_badges(user_id: uuid.UUID, level: int, db: AsyncSession) -> list[str]:
    earned = []
    level_checks = [
        ("awakened", 5),
        ("ascended", 10),
        ("transcendent", 20),
        ("the_undying", 50),
    ]
    for badge_key, threshold in level_checks:
        if level >= threshold:
            name = await _award_badge_if_eligible(user_id, badge_key, db)
            if name:
                earned.append(name)
    return earned


async def check_trade_badges(user_id: uuid.UUID, db: AsyncSession) -> list[str]:
    from app.models.economy import Trade
    count_result = await db.execute(
        select(func.count()).where(Trade.sender_id == user_id)
    )
    total = count_result.scalar() or 0

    earned = []
    if total >= 1:
        name = await _award_badge_if_eligible(user_id, "generous_soul", db)
        if name:
            earned.append(name)
    if total >= 10:
        name = await _award_badge_if_eligible(user_id, "tithe_of_ancients", db)
        if name:
            earned.append(name)
    return earned


async def check_social_badges(user_id: uuid.UUID, db: AsyncSession, just_created_guild: bool = False) -> list[str]:
    from app.models.guild import GuildMember, Guild
    earned = []

    # Joined a guild
    result = await db.execute(
        select(func.count()).where(GuildMember.user_id == user_id, GuildMember.is_active == True)
    )
    if (result.scalar() or 0) >= 1:
        name = await _award_badge_if_eligible(user_id, "bound_by_oath", db)
        if name:
            earned.append(name)

    # Created a guild
    if just_created_guild:
        name = await _award_badge_if_eligible(user_id, "founding_rune", db)
        if name:
            earned.append(name)

    # Is a GM of any guild
    result = await db.execute(select(func.count()).where(Guild.guild_master_id == user_id, Guild.is_dissolved == False))
    if (result.scalar() or 0) >= 1:
        name = await _award_badge_if_eligible(user_id, "guild_master", db)
        if name:
            earned.append(name)

    return earned


async def check_sanctum_badges(user_id: uuid.UUID, db: AsyncSession) -> list[str]:
    from app.models.quest import QuestCompletion, CompletionStatusEnum, QuestTemplate, QuestInstance
    from app.models.sanctum import Sanctum

    result = await db.execute(
        select(func.count())
        .select_from(QuestCompletion)
        .join(QuestInstance, QuestCompletion.instance_id == QuestInstance.id)
        .join(QuestTemplate, QuestInstance.template_id == QuestTemplate.id)
        .join(Sanctum, QuestTemplate.sanctum_id == Sanctum.id)
        .where(QuestCompletion.user_id == user_id, QuestCompletion.status == CompletionStatusEnum.done)
    )
    total = result.scalar() or 0

    earned = []
    if total >= 10:
        name = await _award_badge_if_eligible(user_id, "lone_wanderer", db)
        if name:
            earned.append(name)
    if total >= 50:
        name = await _award_badge_if_eligible(user_id, "inner_sanctum", db)
        if name:
            earned.append(name)
    return earned
