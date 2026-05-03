"""
backend/app/services/notification_service.py

Create and manage in-app notifications.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationCategoryEnum, NotificationSetting


async def _is_category_enabled(user_id: uuid.UUID, category: NotificationCategoryEnum, db: AsyncSession) -> bool:
    result = await db.execute(
        select(NotificationSetting).where(
            NotificationSetting.user_id == user_id,
            NotificationSetting.category == category,
        )
    )
    setting = result.scalar_one_or_none()
    return setting.enabled if setting else True


async def send_notification(
    user_id: uuid.UUID,
    category: NotificationCategoryEnum,
    title: str,
    body: str,
    db: AsyncSession,
    link: str | None = None,
) -> None:
    """Create an in-app notification if the user has the category enabled."""
    if not await _is_category_enabled(user_id, category, db):
        return

    notification = Notification(
        user_id=user_id,
        category=category,
        title=title,
        body=body,
        link=link,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(notification)

    # Invalidate Redis unread cache
    from app.redis_client import get_redis, notif_unread_key
    redis = await get_redis()
    await redis.delete(notif_unread_key(str(user_id)))


async def notify_proposal_created(
    guild_member_ids: list[uuid.UUID],
    proposer_name: str,
    quest_title: str,
    guild_id: uuid.UUID,
    proposal_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    for member_id in guild_member_ids:
        await send_notification(
            user_id=member_id,
            category=NotificationCategoryEnum.proposals_voting,
            title="New Quest Proposal",
            body=f"{proposer_name} proposed '{quest_title}'. Cast your vote.",
            link=f"/guilds/{guild_id}/proposals/{proposal_id}",
            db=db,
        )


async def notify_proposal_resolved(
    user_id: uuid.UUID,
    quest_title: str,
    approved: bool,
    db: AsyncSession,
) -> None:
    if approved:
        body = f"Your quest '{quest_title}' is now active."
    else:
        body = f"'{quest_title}' was not approved by the Guild."
    await send_notification(
        user_id=user_id,
        category=NotificationCategoryEnum.proposals_voting,
        title="Quest Proposal Resolved",
        body=body,
        db=db,
    )


async def notify_level_up(user_id: uuid.UUID, level: int, title: str, db: AsyncSession) -> None:
    await send_notification(
        user_id=user_id,
        category=NotificationCategoryEnum.level_badge,
        title="Level Up!",
        body=f"You reached Level {level} — {title}. The shadows grow in your favour.",
        db=db,
    )


async def notify_badge_earned(user_id: uuid.UUID, badge_name: str, db: AsyncSession) -> None:
    await send_notification(
        user_id=user_id,
        category=NotificationCategoryEnum.level_badge,
        title="Badge Unlocked",
        body=f"Badge unlocked: {badge_name}.",
        db=db,
    )


async def notify_trade_received(
    receiver_id: uuid.UUID,
    sender_name: str,
    amount: int,
    db: AsyncSession,
) -> None:
    await send_notification(
        user_id=receiver_id,
        category=NotificationCategoryEnum.trade_alerts,
        title="Points Received",
        body=f"{sender_name} sent you {amount} points.",
        db=db,
    )


async def notify_guild_membership(
    user_id: uuid.UUID,
    body: str,
    db: AsyncSession,
) -> None:
    await send_notification(
        user_id=user_id,
        category=NotificationCategoryEnum.guild_membership,
        title="Guild Update",
        body=body,
        db=db,
    )


async def get_user_notifications(user_id: uuid.UUID, db: AsyncSession) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id, Notification.expires_at > datetime.now(timezone.utc))
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    return list(result.scalars().all())


async def mark_all_read(user_id: uuid.UUID, db: AsyncSession) -> None:
    await db.execute(
        update(Notification).where(Notification.user_id == user_id).values(is_read=True)
    )
    from app.redis_client import get_redis, notif_unread_key
    redis = await get_redis()
    await redis.delete(notif_unread_key(str(user_id)))
