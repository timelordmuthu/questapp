"""
backend/app/routers/users.py
"""

import uuid

import cloudinary.uploader
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.badge import Badge, UserBadge
from app.models.guild import Guild, GuildMember
from app.models.quest import CompletionStatusEnum, QuestCompletion, QuestInstance, QuestTemplate
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    CompletedQuestHistoryResponse,
    OwnProfileResponse,
    PinQuestRequest,
    PublicProfileResponse,
    UpdateProfileRequest,
)
from app.services.quest_service import pin_quest, unpin_quest
from app.utils.auth import hash_password, verify_password
from app.utils.xp import get_level_title, level_from_total_xp, xp_to_next_level

settings = get_settings()
router = APIRouter()


def _build_public_profile(user: User, badges: list, wall_of_glory: list, guild_names: list) -> dict:
    return {
        "id": user.id,
        "player_name": user.player_name,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "current_level": user.current_level,
        "level_title": get_level_title(user.current_level),
        "total_xp": user.total_xp,
        "xp_to_next_level": xp_to_next_level(user.total_xp),
        "daily_streak": user.daily_streak,
        "weekly_streak": user.weekly_streak,
        "badges": badges,
        "wall_of_glory": wall_of_glory,
        "guild_names": guild_names,
    }


async def _get_badges_for_user(user_id: uuid.UUID, db: AsyncSession) -> list:
    # Get all badge definitions
    all_badges_result = await db.execute(select(Badge))
    all_badges = all_badges_result.scalars().all()

    # Get earned badges
    earned_result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == user_id)
    )
    earned = {ub.badge_id: ub.earned_at for ub in earned_result.scalars().all()}

    badges_out = []
    for b in all_badges:
        is_unlocked = b.id in earned
        badges_out.append({
            "badge_key": b.badge_key,
            "name": b.name if is_unlocked else "???",
            "description": b.description if is_unlocked else b.hint,
            "hint": b.hint,
            "category": b.category.value,
            "icon_symbol": b.icon_symbol if is_unlocked else "◈",
            "earned_at": earned.get(b.id),
            "is_unlocked": is_unlocked,
        })
    return badges_out


async def _get_wall_of_glory(user_id: uuid.UUID, db: AsyncSession) -> list:
    result = await db.execute(
        select(QuestCompletion, QuestTemplate)
        .join(QuestInstance, QuestCompletion.instance_id == QuestInstance.id)
        .join(QuestTemplate, QuestInstance.template_id == QuestTemplate.id)
        .where(QuestCompletion.user_id == user_id, QuestCompletion.is_pinned == True)
        .order_by(QuestCompletion.pin_order.asc())
    )
    items = []
    for completion, template in result.fetchall():
        items.append({
            "completion_id": completion.id,
            "quest_title": template.title,
            "quest_type": template.quest_type.value,
            "points_earned": completion.points_earned,
            "xp_earned": completion.xp_earned,
            "completed_at": completion.completed_at,
            "pin_order": completion.pin_order,
        })
    return items


async def _get_guild_names(user_id: uuid.UUID, db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(Guild.name)
        .join(GuildMember, Guild.id == GuildMember.guild_id)
        .where(GuildMember.user_id == user_id, GuildMember.is_active == True, Guild.is_dissolved == False)
    )
    return [row[0] for row in result.fetchall()]


@router.get("/me", response_model=OwnProfileResponse)
async def get_own_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    badges = await _get_badges_for_user(current_user.id, db)
    wall = await _get_wall_of_glory(current_user.id, db)
    guild_names = await _get_guild_names(current_user.id, db)
    base = _build_public_profile(current_user, badges, wall, guild_names)
    return {
        **base,
        "total_points": current_user.total_points,
        "email": current_user.email,
        "timezone": current_user.timezone,
        "created_at": current_user.created_at,
    }


@router.get("/{player_name}", response_model=PublicProfileResponse)
async def get_public_profile(
    player_name: str,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.player_name == player_name))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    badges = await _get_badges_for_user(user.id, db)
    wall = await _get_wall_of_glory(user.id, db)
    guild_names = await _get_guild_names(user.id, db)
    return _build_public_profile(user, badges, wall, guild_names)


@router.patch("/me", status_code=204)
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updates = {}
    if data.full_name is not None:
        updates["full_name"] = data.full_name.strip()
    if data.timezone is not None:
        updates["timezone"] = data.timezone
    if updates:
        await db.execute(update(User).where(User.id == current_user.id).values(**updates))


@router.post("/me/avatar", status_code=200)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    allowed = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Use JPG, PNG, GIF, or WEBP.")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large. Max 5MB.")

    result = cloudinary.uploader.upload(
        contents,
        folder=settings.cloudinary_upload_folder,
        public_id=f"avatar_{current_user.id}",
        overwrite=True,
        resource_type="image",
    )
    avatar_url = result["secure_url"]
    await db.execute(update(User).where(User.id == current_user.id).values(avatar_url=avatar_url))
    return {"avatar_url": avatar_url}


@router.post("/me/change-password", status_code=204)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect.")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be at least 8 characters.")
    await db.execute(
        update(User).where(User.id == current_user.id).values(password_hash=hash_password(data.new_password))
    )


@router.get("/me/quest-history", response_model=CompletedQuestHistoryResponse)
async def get_quest_history(
    status_filter: str | None = Query(None, alias="status"),
    source: str | None = Query(None),
    quest_type: str | None = Query(None),
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(QuestCompletion, QuestTemplate, Guild)
        .join(QuestInstance, QuestCompletion.instance_id == QuestInstance.id)
        .join(QuestTemplate, QuestInstance.template_id == QuestTemplate.id)
        .outerjoin(Guild, QuestTemplate.guild_id == Guild.id)
        .where(QuestCompletion.user_id == current_user.id)
        .order_by(QuestCompletion.completed_at.desc().nullslast())
    )

    if status_filter and status_filter in ("done", "missed"):
        query = query.where(QuestCompletion.status == CompletionStatusEnum(status_filter))
    if quest_type:
        from app.models.quest import QuestTypeEnum
        query = query.where(QuestTemplate.quest_type == QuestTypeEnum(quest_type))
    if category:
        from app.models.quest import QuestCategoryEnum
        query = query.where(QuestTemplate.category == QuestCategoryEnum(category))

    result = await db.execute(query)
    all_rows = result.fetchall()
    total = len(all_rows)
    paginated = all_rows[(page - 1) * page_size : page * page_size]

    items = []
    for completion, template, guild in paginated:
        items.append({
            "completion_id": completion.id,
            "quest_title": template.title,
            "quest_type": template.quest_type.value,
            "category": template.category.value,
            "source": guild.name if guild else "Sanctum",
            "points_earned": completion.points_earned,
            "xp_earned": completion.xp_earned,
            "completed_at": completion.completed_at,
            "status": completion.status.value,
            "is_pinned": completion.is_pinned,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/me/wall-of-glory/pin", status_code=204)
async def pin_to_wall(
    data: PinQuestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await pin_quest(current_user.id, data.completion_id, data.pin_order, db)


@router.delete("/me/wall-of-glory/{completion_id}", status_code=204)
async def unpin_from_wall(
    completion_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await unpin_quest(current_user.id, completion_id, db)
