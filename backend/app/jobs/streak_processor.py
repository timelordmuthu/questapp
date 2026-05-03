"""
backend/app/jobs/streak_processor.py

Cron: every hour
- Finds expired quest instances with pending completions
- Creates "missed" records for members who didn't complete
- Breaks streaks for users who missed their window
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.guild import GuildMember
from app.models.quest import (
    CompletionStatusEnum,
    QuestCompletion,
    QuestInstance,
    QuestStatusEnum,
    QuestTemplate,
    QuestTypeEnum,
)
from app.models.sanctum import Sanctum
from app.models.user import User


async def process_missed_quests(db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)

    # Find active instances whose deadline has passed
    result = await db.execute(
        select(QuestInstance, QuestTemplate)
        .join(QuestTemplate, QuestInstance.template_id == QuestTemplate.id)
        .where(
            QuestInstance.status == QuestStatusEnum.active,
            QuestInstance.period_end < now,
        )
    )
    expired_rows = result.fetchall()

    for instance, template in expired_rows:
        # Determine which users should have completion records
        if template.guild_id:
            members_result = await db.execute(
                select(GuildMember.user_id).where(
                    GuildMember.guild_id == template.guild_id,
                    GuildMember.is_active == True,
                )
            )
            user_ids = [row[0] for row in members_result.fetchall()]
        else:
            # Sanctum quest — only owner
            sanctum_result = await db.execute(
                select(Sanctum).where(Sanctum.id == template.sanctum_id)
            )
            sanctum = sanctum_result.scalar_one_or_none()
            user_ids = [sanctum.user_id] if sanctum else []

        for user_id in user_ids:
            # Check if already has a completion
            result = await db.execute(
                select(QuestCompletion).where(
                    QuestCompletion.instance_id == instance.id,
                    QuestCompletion.user_id == user_id,
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                # Create missed record
                db.add(QuestCompletion(
                    instance_id=instance.id,
                    user_id=user_id,
                    status=CompletionStatusEnum.missed,
                    points_earned=0,
                    xp_earned=0,
                ))
                # Break streak
                if template.quest_type == QuestTypeEnum.daily:
                    await db.execute(
                        update(User).where(User.id == user_id).values(daily_streak=0)
                    )
                elif template.quest_type == QuestTypeEnum.weekly:
                    await db.execute(
                        update(User).where(User.id == user_id).values(weekly_streak=0)
                    )
            elif existing.status == CompletionStatusEnum.pending:
                # Pending → missed
                await db.execute(
                    update(QuestCompletion)
                    .where(QuestCompletion.id == existing.id)
                    .values(status=CompletionStatusEnum.missed)
                )
                # Break streak
                if template.quest_type == QuestTypeEnum.daily:
                    await db.execute(
                        update(User).where(User.id == user_id).values(daily_streak=0)
                    )
                elif template.quest_type == QuestTypeEnum.weekly:
                    await db.execute(
                        update(User).where(User.id == user_id).values(weekly_streak=0)
                    )

        # Mark instance as completed
        await db.execute(
            update(QuestInstance)
            .where(QuestInstance.id == instance.id)
            .values(status=QuestStatusEnum.completed)
        )

    await db.commit()


async def main():
    async with AsyncSessionLocal() as db:
        print(f"[{datetime.now()}] Running streak processor...")
        await process_missed_quests(db)
        print(f"[{datetime.now()}] Done. Processed expired instances.")


if __name__ == "__main__":
    asyncio.run(main())
