"""
backend/app/jobs/housekeeping.py

Cron: daily at 3 AM UTC
- Purge expired notifications
- Purge guild archives past 90 days
- Expire stale sessions
- Expire used/stale password reset tokens
- Resolve proposals whose voting window closed without quorum
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal


async def purge_expired_notifications(db: AsyncSession) -> int:
    from app.models.notification import Notification
    now = datetime.now(timezone.utc)
    result = await db.execute(delete(Notification).where(Notification.expires_at < now))
    return result.rowcount


async def purge_guild_archives(db: AsyncSession) -> int:
    from app.models.guild import GuildArchive
    now = datetime.now(timezone.utc)
    result = await db.execute(delete(GuildArchive).where(GuildArchive.purge_at < now))
    return result.rowcount


async def expire_stale_sessions(db: AsyncSession) -> int:
    from app.models.user import Session
    now = datetime.now(timezone.utc)
    result = await db.execute(delete(Session).where(Session.expires_at < now))
    return result.rowcount


async def expire_password_reset_tokens(db: AsyncSession) -> int:
    from app.models.user import PasswordResetToken
    now = datetime.now(timezone.utc)
    result = await db.execute(delete(PasswordResetToken).where(PasswordResetToken.expires_at < now))
    return result.rowcount


async def resolve_expired_proposals(db: AsyncSession) -> int:
    """Mark proposals as expired if their voting window closed and they are still pending."""
    from app.models.proposal import QuestProposal, ProposalStatusEnum
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(QuestProposal).where(
            QuestProposal.status == ProposalStatusEnum.pending,
            QuestProposal.voting_closes_at < now,
        )
    )
    expired = result.scalars().all()

    for proposal in expired:
        await db.execute(
            update(QuestProposal)
            .where(QuestProposal.id == proposal.id)
            .values(status=ProposalStatusEnum.expired, resolved_at=now)
        )

    return len(expired)


async def main():
    async with AsyncSessionLocal() as db:
        print(f"[{datetime.now()}] Running housekeeping...")

        n = await purge_expired_notifications(db)
        print(f"  Purged {n} expired notifications.")

        a = await purge_guild_archives(db)
        print(f"  Purged {a} guild archives.")

        s = await expire_stale_sessions(db)
        print(f"  Expired {s} stale sessions.")

        p = await expire_password_reset_tokens(db)
        print(f"  Expired {p} stale password reset tokens.")

        pr = await resolve_expired_proposals(db)
        print(f"  Expired {pr} unresolved proposals.")

        await db.commit()
        print(f"[{datetime.now()}] Housekeeping complete.")


if __name__ == "__main__":
    asyncio.run(main())
