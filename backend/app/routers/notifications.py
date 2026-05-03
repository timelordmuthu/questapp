"""
backend/app/routers/notifications.py
"""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.notification import Notification, NotificationSetting
from app.models.user import User
from app.redis_client import get_redis, notif_unread_key
from app.services.notification_service import get_user_notifications, mark_all_read

router = APIRouter()


@router.get("")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notifications = await get_user_notifications(current_user.id, db)
    return [
        {
            "id": n.id,
            "category": n.category.value,
            "title": n.title,
            "body": n.body,
            "link": n.link,
            "is_read": n.is_read,
            "created_at": n.created_at,
        }
        for n in notifications
    ]


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    redis = await get_redis()
    cached = await redis.get(notif_unread_key(str(current_user.id)))
    if cached is not None:
        return {"unread_count": int(cached)}

    from sqlalchemy import func
    from datetime import datetime, timezone
    result = await db.execute(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
            Notification.expires_at > datetime.now(timezone.utc),
        )
    )
    count = result.scalar() or 0
    await redis.setex(notif_unread_key(str(current_user.id)), 60, str(count))
    return {"unread_count": count}


@router.post("/mark-all-read", status_code=204)
async def mark_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_all_read(current_user.id, db)


@router.patch("/{notification_id}/read", status_code=204)
async def mark_one_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        ).values(is_read=True)
    )
    redis = await get_redis()
    await redis.delete(notif_unread_key(str(current_user.id)))


@router.get("/settings")
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.user_id == current_user.id)
    )
    settings = result.scalars().all()
    return [{"category": s.category.value, "enabled": s.enabled} for s in settings]


@router.patch("/settings", status_code=204)
async def update_notification_setting(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(NotificationSetting)
        .where(NotificationSetting.user_id == current_user.id, NotificationSetting.category == data["category"])
        .values(enabled=data["enabled"])
    )
