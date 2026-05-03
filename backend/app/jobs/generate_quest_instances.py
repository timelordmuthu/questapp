"""
backend/app/jobs/generate_quest_instances.py

Cron: every 5 minutes
- Creates new daily/weekly instances when the current one's period_end has passed (AD-03)
- Unlocks side quests when their unlock_hour_offset window arrives
- Closes expired competition voting and determines winners (AD-10)
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.quest import (
    QuestInstance,
    QuestStatusEnum,
    QuestTemplate,
    QuestTypeEnum,
    SideQuest,
)
from app.utils.timezone import week_end_saturday, week_start_sunday


async def generate_instances(db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)

    # Find active daily/weekly templates whose latest instance has expired
    result = await db.execute(
        select(QuestTemplate).where(
            QuestTemplate.status == QuestStatusEnum.active,
            QuestTemplate.quest_type.in_([QuestTypeEnum.daily, QuestTypeEnum.weekly]),
        )
    )
    templates = result.scalars().all()

    for template in templates:
        # Get the latest instance
        latest_result = await db.execute(
            select(QuestInstance)
            .where(QuestInstance.template_id == template.id)
            .order_by(QuestInstance.period_end.desc())
            .limit(1)
        )
        latest = latest_result.scalar_one_or_none()

        # If latest instance has ended, create the next one
        if latest and latest.period_end < now and latest.status == QuestStatusEnum.active:
            # Mark old instance completed
            await db.execute(
                update(QuestInstance)
                .where(QuestInstance.id == latest.id)
                .values(status=QuestStatusEnum.completed)
            )

            # Create next instance
            if template.quest_type == QuestTypeEnum.daily:
                new_start = latest.period_end + timedelta(seconds=1)
                new_end = new_start.replace(hour=23, minute=59, second=59)
                # Ensure we don't go past a configured deadline
                if template.deadline_at and new_end > template.deadline_at:
                    continue
            else:  # weekly
                week_start_date = week_start_sunday(latest.period_end.date() + timedelta(days=1))
                week_end_date = week_end_saturday(week_start_date)
                new_start = datetime(week_start_date.year, week_start_date.month, week_start_date.day, 0, 0, 0, tzinfo=timezone.utc)
                new_end = datetime(week_end_date.year, week_end_date.month, week_end_date.day, 23, 59, 59, tzinfo=timezone.utc)

            db.add(QuestInstance(
                template_id=template.id,
                period_start=new_start,
                period_end=new_end,
                status=QuestStatusEnum.active,
            ))

    await db.commit()


async def unlock_side_quests(db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(SideQuest).where(
            SideQuest.status == "locked",
            SideQuest.unlocks_at <= now,
        )
    )
    side_quests = result.scalars().all()
    for sq in side_quests:
        await db.execute(
            update(SideQuest).where(SideQuest.id == sq.id).values(status="active")
        )
        # Notify guild members of side quest unlock
        parent_result = await db.execute(select(QuestTemplate).where(QuestTemplate.id == sq.parent_template_id))
        parent = parent_result.scalar_one_or_none()
        if parent and parent.guild_id:
            from app.models.guild import GuildMember
            from app.models.notification import NotificationCategoryEnum
            from app.services.notification_service import send_notification
            members_result = await db.execute(
                select(GuildMember.user_id).where(
                    GuildMember.guild_id == parent.guild_id,
                    GuildMember.is_active == True,
                )
            )
            for (member_id,) in members_result.fetchall():
                await send_notification(
                    user_id=member_id,
                    category=NotificationCategoryEnum.proposals_voting,
                    title="Side Quest Unlocked",
                    body=f"A hidden secret has emerged within '{parent.title}'.",
                    link=f"/guilds/{parent.guild_id}",
                    db=db,
                )
    await db.commit()


async def close_expired_competition_voting(db: AsyncSession) -> None:
    """AD-10: Determine competition winners when voting period closes."""
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(QuestInstance, QuestTemplate)
        .join(QuestTemplate, QuestInstance.template_id == QuestTemplate.id)
        .where(
            QuestTemplate.quest_type == QuestTypeEnum.competition,
            QuestInstance.status == QuestStatusEnum.active,
            QuestInstance.period_end < now,
        )
    )
    rows = result.fetchall()

    for instance, template in rows:
        from sqlalchemy import func
        from app.models.competition import CompetitionVote
        from app.models.quest import QuestCompletion, CompletionStatusEnum

        # Count winner votes
        votes_result = await db.execute(
            select(CompetitionVote.winner_vote, func.count().label("cnt"))
            .where(CompetitionVote.instance_id == instance.id)
            .group_by(CompetitionVote.winner_vote)
            .order_by(func.count().desc())
        )
        vote_rows = votes_result.fetchall()

        if not vote_rows:
            # 0 votes — close with no winners
            await db.execute(update(QuestInstance).where(QuestInstance.id == instance.id).values(status=QuestStatusEnum.completed))
            continue

        winner_id, winner_votes = vote_rows[0]
        tie = len(vote_rows) > 1 and vote_rows[1][1] == winner_votes

        if not tie and winner_id and template.winner_point_reward:
            # Award winner
            winner_result = await db.execute(select(__import__("app.models.user", fromlist=["User"]).User).where(__import__("app.models.user", fromlist=["User"]).User.id == winner_id))
            winner = winner_result.scalar_one_or_none()
            if winner:
                from app.services.economy_service import award_points_and_xp
                await award_points_and_xp(
                    user=winner,
                    points=template.winner_point_reward,
                    xp=0,
                    quest_type="competition",
                    reference_id=instance.id,
                    reference_type="competition_winner",
                    description=f"Competition winner: {template.title}",
                    guild_id=template.guild_id,
                    db=db,
                )
                # Badge: warchief
                from app.services.badge_service import _award_badge_if_eligible
                from app.services.notification_service import notify_badge_earned
                badge_name = await _award_badge_if_eligible(winner_id, "warchief", db)
                if badge_name:
                    await notify_badge_earned(winner_id, badge_name, db)

        await db.execute(update(QuestInstance).where(QuestInstance.id == instance.id).values(status=QuestStatusEnum.completed))

    await db.commit()


async def main():
    async with AsyncSessionLocal() as db:
        print(f"[{datetime.now()}] Running quest instance generator...")
        await generate_instances(db)
        await unlock_side_quests(db)
        await close_expired_competition_voting(db)
        print(f"[{datetime.now()}] Done.")


if __name__ == "__main__":
    asyncio.run(main())
