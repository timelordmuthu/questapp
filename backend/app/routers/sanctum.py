"""
backend/app/routers/sanctum.py
"""

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.quest import QuestInstance, QuestStatusEnum, QuestTemplate, QuestTypeEnum, QuestCategoryEnum
from app.models.sanctum import Sanctum
from app.models.user import User
from app.schemas.quest import QuestCreateRequest
from app.services.quest_service import mark_quest_done
from app.utils.timezone import week_start_sunday, week_end_saturday

router = APIRouter()


@router.post("/quests", status_code=201)
async def create_sanctum_quest(
    data: QuestCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sanctum quests activate immediately — no approval."""
    result = await db.execute(select(Sanctum).where(Sanctum.user_id == current_user.id))
    sanctum = result.scalar_one_or_none()
    if not sanctum:
        raise HTTPException(status_code=500, detail="Sanctum not found.")

    now = datetime.now(timezone.utc)
    start = max(data.start_at, now)

    if data.quest_type == QuestTypeEnum.daily:
        period_end = data.deadline_at or start.replace(hour=23, minute=59, second=59)
    elif data.quest_type == QuestTypeEnum.weekly:
        week_s = week_start_sunday(start.date())
        week_e = week_end_saturday(week_s)
        period_end = data.deadline_at or datetime(week_e.year, week_e.month, week_e.day, 23, 59, 59, tzinfo=timezone.utc)
    else:
        period_end = data.deadline_at or (start + timedelta(days=30))

    template = QuestTemplate(
        sanctum_id=sanctum.id,
        proposed_by=current_user.id,
        title=data.title,
        description=data.description,
        quest_type=QuestTypeEnum(data.quest_type),
        category=QuestCategoryEnum(data.category),
        category_custom_label=data.category_custom_label,
        point_worth=data.point_worth,
        xp_worth=data.xp_worth,
        start_at=start,
        deadline_at=data.deadline_at,
        status=QuestStatusEnum.active,
    )
    db.add(template)
    await db.flush()

    instance = QuestInstance(
        template_id=template.id,
        period_start=start,
        period_end=period_end,
        status=QuestStatusEnum.active,
    )
    db.add(instance)
    return {"template_id": str(template.id), "instance_id": str(instance.id)}


@router.get("/quests")
async def list_sanctum_quests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Sanctum).where(Sanctum.user_id == current_user.id))
    sanctum = result.scalar_one_or_none()
    result = await db.execute(
        select(QuestTemplate).where(
            QuestTemplate.sanctum_id == sanctum.id,
            QuestTemplate.status == QuestStatusEnum.active,
        )
    )
    return [{"id": t.id, "title": t.title, "quest_type": t.quest_type.value} for t in result.scalars().all()]


@router.post("/{instance_id}/mark-done")
async def mark_sanctum_quest_done(
    instance_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mark_quest_done(instance_id, current_user, db)
