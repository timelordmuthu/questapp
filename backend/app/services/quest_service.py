"""
backend/app/services/quest_service.py

Quest completion, streak updates, Wall of Glory pinning.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quest import (
    CompletionStatusEnum,
    QuestCompletion,
    QuestInstance,
    QuestStatusEnum,
    QuestTemplate,
    QuestTypeEnum,
)
from app.models.streak import DailyStreakLog, WeeklyStreakLog
from app.models.user import User
from app.utils.timezone import today_in_tz, week_start_sunday
from app.utils.xp import apply_xp, get_streak_multiplier


async def mark_quest_done(
    instance_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> dict:
    """
    Mark a quest instance as done for the current user.
    Handles points/XP awarding, streak update, badge checks.
    """
    # Load instance + template
    result = await db.execute(
        select(QuestInstance).where(QuestInstance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quest instance not found.")

    if instance.status != QuestStatusEnum.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This quest is not currently active.")

    now = datetime.now(timezone.utc)
    if instance.period_end < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quest deadline has passed.")

    result = await db.execute(select(QuestTemplate).where(QuestTemplate.id == instance.template_id))
    template = result.scalar_one_or_none()

    # Load or create completion record
    result = await db.execute(
        select(QuestCompletion).where(
            QuestCompletion.instance_id == instance_id,
            QuestCompletion.user_id == user.id,
        )
    )
    completion = result.scalar_one_or_none()

    if completion and completion.status == CompletionStatusEnum.done:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already marked done.")

    # Determine multiplier
    quest_type = template.quest_type.value
    if quest_type == "daily":
        multiplier = get_streak_multiplier(user.daily_streak)
    elif quest_type == "weekly":
        multiplier = get_streak_multiplier(user.weekly_streak)
    else:
        multiplier = 1.0

    import math
    final_xp = math.floor(template.xp_worth * multiplier)
    points_earned = template.point_worth

    if completion:
        await db.execute(
            update(QuestCompletion).where(QuestCompletion.id == completion.id).values(
                status=CompletionStatusEnum.done,
                points_earned=points_earned,
                xp_earned=final_xp,
                completed_at=now,
                streak_multiplier_applied=multiplier,
            )
        )
    else:
        completion = QuestCompletion(
            instance_id=instance_id,
            user_id=user.id,
            status=CompletionStatusEnum.done,
            points_earned=points_earned,
            xp_earned=final_xp,
            completed_at=now,
            streak_multiplier_applied=multiplier,
        )
        db.add(completion)

    await db.flush()

    # Award points and XP
    guild_id = template.guild_id
    from app.services.economy_service import award_points_and_xp
    economy_result = await award_points_and_xp(
        user=user,
        points=points_earned,
        xp=template.xp_worth,
        quest_type=quest_type,
        reference_id=instance_id,
        reference_type="quest_instance",
        description=f"Quest: {template.title}",
        guild_id=guild_id,
        db=db,
    )

    # Update streaks
    await _update_streaks(user, template.quest_type, db)

    # Reload user to get updated values
    result = await db.execute(select(User).where(User.id == user.id))
    updated_user = result.scalar_one()

    # Badge checks (event-driven, AD-09)
    from app.services import badge_service
    from app.services.notification_service import notify_badge_earned, notify_level_up
    from app.utils.xp import get_level_title

    badges_earned = await badge_service.check_quest_badges(user.id, db)
    badges_earned += await badge_service.check_streak_badges(
        user.id, updated_user.daily_streak, updated_user.weekly_streak, db
    )
    if economy_result["level_up"]:
        badges_earned += await badge_service.check_level_badges(user.id, economy_result["new_level"], db)
        level_title = get_level_title(economy_result["new_level"])
        await notify_level_up(user.id, economy_result["new_level"], level_title, db)

    for badge_name in badges_earned:
        await notify_badge_earned(user.id, badge_name, db)

    # Sanctum-specific badge check
    if template.sanctum_id:
        badges_earned += await badge_service.check_sanctum_badges(user.id, db)

    # Group quest progress notification
    if template.quest_type == QuestTypeEnum.group:
        await _notify_group_progress(instance, template, user, db)

    return {
        "message": "Quest marked as done!",
        **economy_result,
        "badges_earned": badges_earned,
    }


async def _update_streaks(user: User, quest_type: QuestTypeEnum, db: AsyncSession) -> None:
    """Update daily or weekly streak after a completion."""
    now_date = today_in_tz(user.timezone)

    if quest_type == QuestTypeEnum.daily:
        # Check if already credited today
        if user.last_daily_streak_date and user.last_daily_streak_date == now_date:
            return
        # Check continuity (yesterday must have been credited, or first day)
        from datetime import timedelta
        yesterday = now_date - timedelta(days=1)
        if user.last_daily_streak_date == yesterday:
            new_streak = user.daily_streak + 1
        else:
            new_streak = 1  # reset

        await db.execute(
            update(User).where(User.id == user.id).values(
                daily_streak=new_streak,
                last_daily_streak_date=now_date,
            )
        )
        # Log streak entry
        db.add(DailyStreakLog(user_id=user.id, streak_date=now_date, streak_value=new_streak))

    elif quest_type == QuestTypeEnum.weekly:
        week_start = week_start_sunday(now_date)
        if user.last_weekly_streak_date and user.last_weekly_streak_date == week_start:
            return
        # Continuity: last week's Sunday must be exactly 7 days ago
        from datetime import timedelta
        last_week_start = week_start - timedelta(weeks=1)
        if user.last_weekly_streak_date == last_week_start:
            new_streak = user.weekly_streak + 1
        else:
            new_streak = 1

        await db.execute(
            update(User).where(User.id == user.id).values(
                weekly_streak=new_streak,
                last_weekly_streak_date=week_start,
            )
        )
        db.add(WeeklyStreakLog(user_id=user.id, week_start=week_start, streak_value=new_streak))


async def _notify_group_progress(instance: QuestInstance, template: QuestTemplate, user: User, db: AsyncSession) -> None:
    """Notify guild members of group quest progress."""
    from app.models.guild import GuildMember
    from app.services.notification_service import send_notification
    from app.models.notification import NotificationCategoryEnum

    # Count completions
    done_count = await db.execute(
        select(func.count()).where(
            QuestCompletion.instance_id == instance.id,
            QuestCompletion.status == CompletionStatusEnum.done,
        )
    )
    done_total = done_count.scalar() or 0

    total_count = await db.execute(
        select(func.count()).where(GuildMember.guild_id == template.guild_id, GuildMember.is_active == True)
    )
    total = total_count.scalar() or 0

    # Get guild members to notify
    result = await db.execute(
        select(GuildMember.user_id).where(GuildMember.guild_id == template.guild_id, GuildMember.is_active == True)
    )
    member_ids = [row[0] for row in result.fetchall()]

    if done_total == total:
        body = f"Your entire Guild completed '{template.title}'. Glory to all."
    else:
        body = f"{user.player_name} completed '{template.title}'. {done_total}/{total} members done."

    for member_id in member_ids:
        if member_id != user.id:
            await send_notification(
                user_id=member_id,
                category=NotificationCategoryEnum.group_progress,
                title="Group Quest Update",
                body=body,
                link=f"/guilds/{template.guild_id}",
                db=db,
            )


async def pin_quest(
    user_id: uuid.UUID,
    completion_id: uuid.UUID,
    pin_order: int,
    db: AsyncSession,
) -> None:
    """Pin a completed quest to Wall of Glory (max 3, AD-06)."""
    if pin_order not in (1, 2, 3):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pin order must be 1, 2, or 3.")

    result = await db.execute(
        select(QuestCompletion).where(
            QuestCompletion.id == completion_id,
            QuestCompletion.user_id == user_id,
            QuestCompletion.status == CompletionStatusEnum.done,
        )
    )
    completion = result.scalar_one_or_none()
    if not completion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Completion not found or not 'done'.")

    # Count current pins (AD-06: app-layer enforcement of 3-pin limit)
    count_result = await db.execute(
        select(func.count()).where(
            QuestCompletion.user_id == user_id,
            QuestCompletion.is_pinned == True,
        )
    )
    current_pins = count_result.scalar() or 0

    if current_pins >= 3 and not completion.is_pinned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unpin an existing Wall of Glory quest first (max 3 pins).",
        )

    await db.execute(
        update(QuestCompletion).where(QuestCompletion.id == completion_id).values(
            is_pinned=True, pin_order=pin_order
        )
    )


async def unpin_quest(user_id: uuid.UUID, completion_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(
        select(QuestCompletion).where(QuestCompletion.id == completion_id, QuestCompletion.user_id == user_id)
    )
    completion = result.scalar_one_or_none()
    if not completion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Completion not found.")
    await db.execute(
        update(QuestCompletion).where(QuestCompletion.id == completion_id).values(is_pinned=False, pin_order=None)
    )
