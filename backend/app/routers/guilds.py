"""
backend/app/routers/guilds.py
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.guild import Guild, GuildMember
from app.models.user import User
from app.schemas.guild import (
    GuildCreateRequest,
    GuildJoinRequest,
    GuildResponse,
    GuildUpdateRequest,
    TransferGuildMasterRequest,
)
from app.services import guild_service
from app.services.badge_service import check_social_badges
from app.services.notification_service import notify_badge_earned, notify_guild_membership
from app.utils.xp import get_level_title

router = APIRouter()


@router.post("", status_code=201)
async def create_guild(
    data: GuildCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    guild = await guild_service.create_guild(data.name, current_user, db)
    badges = await check_social_badges(current_user.id, db, just_created_guild=True)
    for b in badges:
        await notify_badge_earned(current_user.id, b, db)
    return {"id": str(guild.id), "name": guild.name, "sigil_code": guild.sigil_code}


@router.post("/join", status_code=200)
async def join_guild(
    data: GuildJoinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    guild = await guild_service.join_guild(data.sigil_code, current_user, db)

    # Notify existing members
    result = await db.execute(
        select(GuildMember.user_id).where(
            GuildMember.guild_id == guild.id,
            GuildMember.is_active == True,
            GuildMember.user_id != current_user.id,
        )
    )
    for (member_id,) in result.fetchall():
        await notify_guild_membership(member_id, f"{current_user.player_name} joined {guild.name}.", db)

    badges = await check_social_badges(current_user.id, db)
    for b in badges:
        await notify_badge_earned(current_user.id, b, db)

    return {"id": str(guild.id), "name": guild.name}


@router.get("/{guild_id}", response_model=GuildResponse)
async def get_guild(
    guild_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Guild).where(Guild.id == guild_id, Guild.is_dissolved == False))
    guild = result.scalar_one_or_none()
    if not guild:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guild not found.")

    # Verify membership
    result = await db.execute(
        select(GuildMember).where(GuildMember.guild_id == guild_id, GuildMember.user_id == current_user.id, GuildMember.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this Guild.")

    # Load members
    result = await db.execute(
        select(GuildMember, User)
        .join(User, GuildMember.user_id == User.id)
        .where(GuildMember.guild_id == guild_id, GuildMember.is_active == True)
        .order_by(GuildMember.joined_at.asc())
    )
    members = []
    for gm, u in result.fetchall():
        members.append({
            "user_id": u.id,
            "player_name": u.player_name,
            "full_name": u.full_name,
            "avatar_url": u.avatar_url,
            "current_level": u.current_level,
            "level_title": get_level_title(u.current_level),
            "joined_at": gm.joined_at,
            "last_active_at": u.last_active_at,
            "is_guild_master": str(u.id) == str(guild.guild_master_id),
        })

    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count()).where(GuildMember.guild_id == guild_id, GuildMember.is_active == True)
    )

    return {
        "id": guild.id,
        "name": guild.name,
        "sigil_code": guild.sigil_code if str(current_user.id) == str(guild.guild_master_id) else "••••••••",
        "guild_master_id": guild.guild_master_id,
        "max_points_per_quest": guild.max_points_per_quest,
        "max_xp_per_quest": guild.max_xp_per_quest,
        "member_count": count_result.scalar() or 0,
        "members": members,
        "created_at": guild.created_at,
    }


@router.patch("/{guild_id}", status_code=204)
async def update_guild(
    guild_id: uuid.UUID,
    data: GuildUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Guild).where(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    if not guild or str(guild.guild_master_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Guild Master can update settings.")
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if updates:
        from sqlalchemy import update as sa_update
        await db.execute(sa_update(Guild).where(Guild.id == guild_id).values(**updates))


@router.post("/{guild_id}/leave", status_code=204)
async def leave_guild(
    guild_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await guild_service.leave_guild(guild_id, current_user, db)


@router.delete("/{guild_id}/members/{user_id}", status_code=204)
async def remove_member(
    guild_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await guild_service.remove_member(guild_id, user_id, current_user, db)
    await notify_guild_membership(user_id, f"You have been removed from the Guild.", db)


@router.post("/{guild_id}/transfer-master", status_code=204)
async def transfer_master(
    guild_id: uuid.UUID,
    data: TransferGuildMasterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await guild_service.transfer_guild_master(guild_id, data.new_gm_user_id, current_user, db)
    badges = await check_social_badges(data.new_gm_user_id, db)
    for b in badges:
        await notify_badge_earned(data.new_gm_user_id, b, db)


@router.post("/{guild_id}/regenerate-sigil", status_code=200)
async def regenerate_sigil(
    guild_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    code = await guild_service.regenerate_sigil_code(guild_id, current_user, db)
    return {"sigil_code": code}


@router.delete("/{guild_id}", status_code=204)
async def dissolve_guild(
    guild_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Notify members before dissolving
    result = await db.execute(
        select(GuildMember.user_id, Guild.name)
        .join(Guild, GuildMember.guild_id == Guild.id)
        .where(GuildMember.guild_id == guild_id, GuildMember.is_active == True)
    )
    rows = result.fetchall()
    guild_name = rows[0][1] if rows else "Guild"
    for (member_id, _) in rows:
        if member_id != current_user.id:
            await notify_guild_membership(member_id, f"{guild_name} has been dissolved.", db)
    await guild_service.dissolve_guild(guild_id, current_user, db)
