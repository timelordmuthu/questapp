"""
backend/app/routers/quests.py
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.guild import GuildMember
from app.models.quest import (
    CompletionStatusEnum,
    QuestCompletion,
    QuestInstance,
    QuestStatusEnum,
    QuestTemplate,
    QuestTypeEnum,
)
from app.models.user import User
from app.schemas.quest import MarkDoneResponse
from app.services.quest_service import mark_quest_done

router = APIRouter()


@router.get("/feed")
async def get_quest_feed(
    quest_type: str | None = Query(None),
    source: str | None = Query(None),
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Combined active quest feed for user's Sanctum + all joined Guilds.
    Ordered by least time remaining (most urgent first).
    """
    now = datetime.now(timezone.utc)

    # Get user's guild IDs
    guild_result = await db.execute(
        select(GuildMember.guild_id).where(GuildMember.user_id == current_user.id, GuildMember.is_active == True)
    )
    guild_ids = [row[0] for row in guild_result.fetchall()]

    # Build query for active instances in user's guilds + sanctum
    from app.models.sanctum import Sanctum
    sanctum_result = await db.execute(select(Sanctum).where(Sanctum.user_id == current_user.id))
    sanctum = sanctum_result.scalar_one_or_none()
    sanctum_id = sanctum.id if sanctum else None

    query = (
        select(QuestInstance, QuestTemplate, QuestCompletion)
        .join(QuestTemplate, QuestInstance.template_id == QuestTemplate.id)
        .outerjoin(
            QuestCompletion,
            (QuestCompletion.instance_id == QuestInstance.id) & (QuestCompletion.user_id == current_user.id),
        )
        .where(
            QuestInstance.status == QuestStatusEnum.active,
            QuestInstance.period_end > now,
        )
    )

    # Filter to user's scope
    from sqlalchemy import or_
    scope_filters = []
    if guild_ids:
        scope_filters.append(QuestTemplate.guild_id.in_(guild_ids))
    if sanctum_id:
        scope_filters.append(QuestTemplate.sanctum_id == sanctum_id)
    if scope_filters:
        query = query.where(or_(*scope_filters))

    if quest_type:
        query = query.where(QuestTemplate.quest_type == QuestTypeEnum(quest_type))

    # Order by urgency
    query = query.order_by(QuestInstance.period_end.asc())

    result = await db.execute(query)
    rows = result.fetchall()

    # Load guild names for display
    from app.models.guild import Guild
    guild_names_result = await db.execute(select(Guild.id, Guild.name).where(Guild.id.in_(guild_ids)))
    guild_name_map = {str(row[0]): row[1] for row in guild_names_result.fetchall()}

    cards = []
    for instance, template, completion in rows:
        # Completion status
        comp_status = completion.status.value if completion else "pending"

        source_name = guild_name_map.get(str(template.guild_id), "Sanctum") if template.guild_id else "Sanctum"

        # Group progress
        group_done = group_total = None
        if template.quest_type == QuestTypeEnum.group:
            from sqlalchemy import func
            done_r = await db.execute(
                select(func.count()).where(QuestCompletion.instance_id == instance.id, QuestCompletion.status == CompletionStatusEnum.done)
            )
            total_r = await db.execute(
                select(func.count()).where(GuildMember.guild_id == template.guild_id, GuildMember.is_active == True)
            )
            group_done = done_r.scalar() or 0
            group_total = total_r.scalar() or 0

        cards.append({
            "instance_id": instance.id,
            "template_id": template.id,
            "title": template.title,
            "quest_type": template.quest_type.value,
            "category": template.category.value,
            "category_custom_label": template.category_custom_label,
            "source": source_name,
            "point_worth": template.point_worth,
            "xp_worth": template.xp_worth,
            "period_start": instance.period_start,
            "period_end": instance.period_end,
            "completion_status": comp_status,
            "points_earned": completion.points_earned if completion else 0,
            "xp_earned": completion.xp_earned if completion else 0,
            "group_total": group_total,
            "group_done": group_done,
            "is_competition": template.quest_type == QuestTypeEnum.competition,
            "voting_open": None,
        })

    # Paginate
    total = len(cards)
    paginated = cards[(page - 1) * page_size : page * page_size]
    return {"items": paginated, "total": total, "page": page, "page_size": page_size}


@router.post("/{instance_id}/mark-done", response_model=MarkDoneResponse)
async def mark_done(
    instance_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mark_quest_done(instance_id, current_user, db)


@router.post("/{instance_id}/competition-vote")
async def submit_competition_vote(
    instance_id: uuid.UUID,
    winner_id: uuid.UUID,
    runner_up_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.competition import CompetitionVote
    from sqlalchemy import update as sa_update

    # Check existing vote
    result = await db.execute(
        select(CompetitionVote).where(
            CompetitionVote.instance_id == instance_id,
            CompetitionVote.voter_id == current_user.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        await db.execute(
            sa_update(CompetitionVote).where(CompetitionVote.id == existing.id).values(
                winner_vote=winner_id, runner_up_vote=runner_up_id
            )
        )
    else:
        db.add(CompetitionVote(
            instance_id=instance_id,
            voter_id=current_user.id,
            winner_vote=winner_id,
            runner_up_vote=runner_up_id,
        ))
    return {"message": "Vote recorded."}
