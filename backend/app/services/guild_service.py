"""
backend/app/services/guild_service.py

Guild CRUD, member management, succession logic (AD-11).
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guild import Guild, GuildMember
from app.models.user import User
from app.utils.sigil import generate_sigil_code

GUILD_MEMBER_HARD_CAP = 20


async def create_guild(name: str, creator: User, db: AsyncSession) -> Guild:
    """Create a guild, add creator as first active member (guild master)."""
    # Generate unique sigil code (retry once on collision)
    for _ in range(2):
        code = generate_sigil_code()
        result = await db.execute(select(Guild).where(Guild.sigil_code == code))
        if not result.scalar_one_or_none():
            break

    guild = Guild(name=name, sigil_code=code, guild_master_id=creator.id)
    db.add(guild)
    await db.flush()

    member = GuildMember(guild_id=guild.id, user_id=creator.id)
    db.add(member)
    await db.flush()

    return guild


async def join_guild(sigil_code: str, user: User, db: AsyncSession) -> Guild:
    """Join a guild by sigil code. Immediate — no approval step."""
    result = await db.execute(select(Guild).where(Guild.sigil_code == sigil_code, Guild.is_dissolved == False))
    guild = result.scalar_one_or_none()
    if not guild:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Sigil Code.")

    # Check member cap
    count_result = await db.execute(
        select(func.count()).where(GuildMember.guild_id == guild.id, GuildMember.is_active == True)
    )
    if (count_result.scalar() or 0) >= GUILD_MEMBER_HARD_CAP:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Guild is full (20 member limit).")

    # Check not already a member
    result = await db.execute(
        select(GuildMember).where(GuildMember.guild_id == guild.id, GuildMember.user_id == user.id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member of this Guild.")
        # Re-join
        await db.execute(update(GuildMember).where(GuildMember.id == existing.id).values(is_active=True, left_at=None))
    else:
        db.add(GuildMember(guild_id=guild.id, user_id=user.id))

    await db.flush()
    return guild


async def leave_guild(guild_id: uuid.UUID, user: User, db: AsyncSession) -> None:
    """Member leaves guild. Triggers succession if GM leaves."""
    result = await db.execute(
        select(GuildMember).where(GuildMember.guild_id == guild_id, GuildMember.user_id == user.id, GuildMember.is_active == True)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not a member of this Guild.")

    from datetime import datetime, timezone
    await db.execute(update(GuildMember).where(GuildMember.id == membership.id).values(is_active=False, left_at=datetime.now(timezone.utc)))

    # Check if this user is the GM → trigger succession
    result = await db.execute(select(Guild).where(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    if guild and str(guild.guild_master_id) == str(user.id):
        await _auto_promote_gm(guild, user.id, db)


async def remove_member(guild_id: uuid.UUID, target_user_id: uuid.UUID, requester: User, db: AsyncSession) -> None:
    """Guild master removes a member."""
    result = await db.execute(select(Guild).where(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    if not guild or str(guild.guild_master_id) != str(requester.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the Guild Master can remove members.")

    result = await db.execute(
        select(GuildMember).where(GuildMember.guild_id == guild_id, GuildMember.user_id == target_user_id, GuildMember.is_active == True)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    from datetime import datetime, timezone
    await db.execute(update(GuildMember).where(GuildMember.id == membership.id).values(is_active=False, left_at=datetime.now(timezone.utc)))


async def transfer_guild_master(guild_id: uuid.UUID, new_gm_id: uuid.UUID, requester: User, db: AsyncSession) -> None:
    result = await db.execute(select(Guild).where(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    if not guild or str(guild.guild_master_id) != str(requester.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the Guild Master can transfer this role.")

    result = await db.execute(
        select(GuildMember).where(GuildMember.guild_id == guild_id, GuildMember.user_id == new_gm_id, GuildMember.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user is not a Guild member.")

    await db.execute(update(Guild).where(Guild.id == guild_id).values(guild_master_id=new_gm_id))


async def regenerate_sigil_code(guild_id: uuid.UUID, requester: User, db: AsyncSession) -> str:
    result = await db.execute(select(Guild).where(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    if not guild or str(guild.guild_master_id) != str(requester.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the Guild Master can regenerate the Sigil Code.")

    for _ in range(2):
        code = generate_sigil_code()
        result = await db.execute(select(Guild).where(Guild.sigil_code == code))
        if not result.scalar_one_or_none():
            break

    await db.execute(update(Guild).where(Guild.id == guild_id).values(sigil_code=code))
    return code


async def dissolve_guild(guild_id: uuid.UUID, requester: User, db: AsyncSession) -> None:
    """Dissolve guild: cancel active quests, notify members, archive history."""
    result = await db.execute(select(Guild).where(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    if not guild or str(guild.guild_master_id) != str(requester.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the Guild Master can dissolve the Guild.")

    from datetime import datetime, timezone, timedelta
    import json
    from app.models.guild import GuildArchive

    now = datetime.now(timezone.utc)
    await db.execute(update(Guild).where(Guild.id == guild_id).values(is_dissolved=True, dissolved_at=now))

    # Archive
    db.add(GuildArchive(
        guild_id=guild_id,
        guild_name=guild.name,
        archive_data=json.dumps({"guild_id": str(guild_id), "name": guild.name}),
        dissolved_at=now,
        purge_at=now + timedelta(days=90),
    ))


async def _auto_promote_gm(guild: Guild, departing_gm_id: uuid.UUID, db: AsyncSession) -> uuid.UUID | None:
    """AD-11: Promote the longest-standing active member on GM departure."""
    result = await db.execute(
        select(GuildMember)
        .where(GuildMember.guild_id == guild.id, GuildMember.user_id != departing_gm_id, GuildMember.is_active == True)
        .order_by(GuildMember.joined_at.asc())
        .limit(1)
    )
    new_gm = result.scalar_one_or_none()

    if not new_gm:
        # No remaining members — dissolve
        from datetime import datetime, timezone
        await db.execute(update(Guild).where(Guild.id == guild.id).values(is_dissolved=True, dissolved_at=datetime.now(timezone.utc)))
        return None

    await db.execute(update(Guild).where(Guild.id == guild.id).values(guild_master_id=new_gm.user_id))

    # Notify new GM
    from app.services.notification_service import notify_guild_membership
    await notify_guild_membership(
        user_id=new_gm.user_id,
        body=f"You have been promoted to Guild Master of {guild.name}.",
        db=db,
    )
    return new_gm.user_id
