"""
backend/app/services/proposal_service.py

Quest proposal creation, voting, and resolution.
"""

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guild import Guild, GuildMember
from app.models.proposal import (
    ProposalStatusEnum,
    ProposalTypeEnum,
    ProposalVote,
    QuestProposal,
    VoteEnum,
)
from app.models.quest import QuestTemplate, QuestStatusEnum
from app.models.user import User
from app.schemas.quest import QuestCreateRequest
from app.utils.vote import resolve_proposal


async def create_proposal(
    guild_id: uuid.UUID,
    quest_data: QuestCreateRequest,
    proposer: User,
    db: AsyncSession,
) -> QuestProposal:
    """Create a quest proposal. Validates guild caps before submission."""
    result = await db.execute(select(Guild).where(Guild.id == guild_id, Guild.is_dissolved == False))
    guild = result.scalar_one_or_none()
    if not guild:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guild not found.")

    # Verify proposer is a member
    result = await db.execute(
        select(GuildMember).where(
            GuildMember.guild_id == guild_id,
            GuildMember.user_id == proposer.id,
            GuildMember.is_active == True,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this Guild.")

    # Guild cap validation
    if quest_data.point_worth > guild.max_points_per_quest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Point worth exceeds this Guild's cap of {guild.max_points_per_quest}.",
        )
    if quest_data.xp_worth > guild.max_xp_per_quest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"XP worth exceeds this Guild's cap of {guild.max_xp_per_quest}.",
        )

    # Competition requires minimum 3 members
    if quest_data.quest_type.value == "competition":
        from sqlalchemy import func
        count_result = await db.execute(
            select(func.count()).where(GuildMember.guild_id == guild_id, GuildMember.is_active == True)
        )
        if (count_result.scalar() or 0) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Competition quests require at least 3 Guild members.",
            )

    proposal = QuestProposal(
        guild_id=guild_id,
        proposed_by=proposer.id,
        proposal_type=ProposalTypeEnum.create,
        proposed_data=json.dumps(quest_data.model_dump(mode="json")),
        voting_closes_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(proposal)
    await db.flush()

    # Notify all guild members
    result = await db.execute(
        select(GuildMember.user_id).where(GuildMember.guild_id == guild_id, GuildMember.is_active == True)
    )
    member_ids = [row[0] for row in result.fetchall()]

    from app.services.notification_service import notify_proposal_created
    await notify_proposal_created(
        guild_member_ids=member_ids,
        proposer_name=proposer.player_name,
        quest_title=quest_data.title,
        guild_id=guild_id,
        proposal_id=proposal.id,
        db=db,
    )

    return proposal


async def cast_vote(
    proposal_id: uuid.UUID,
    vote: str,
    notes: str | None,
    voter: User,
    db: AsyncSession,
) -> dict:
    """Cast or update a vote on a proposal. Triggers auto-resolution if quorum met."""
    result = await db.execute(
        select(QuestProposal).where(
            QuestProposal.id == proposal_id,
            QuestProposal.status == ProposalStatusEnum.pending,
        )
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found or already resolved.")

    if datetime.now(timezone.utc) > proposal.voting_closes_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voting window has closed.")

    # Verify voter is guild member
    result = await db.execute(
        select(GuildMember).where(
            GuildMember.guild_id == proposal.guild_id,
            GuildMember.user_id == voter.id,
            GuildMember.is_active == True,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this Guild.")

    vote_enum = VoteEnum(vote)

    # Upsert vote
    result = await db.execute(
        select(ProposalVote).where(
            ProposalVote.proposal_id == proposal_id,
            ProposalVote.user_id == voter.id,
        )
    )
    existing_vote = result.scalar_one_or_none()
    if existing_vote:
        await db.execute(
            update(ProposalVote).where(ProposalVote.id == existing_vote.id).values(vote=vote_enum, notes=notes)
        )
    else:
        db.add(ProposalVote(proposal_id=proposal_id, user_id=voter.id, vote=vote_enum, notes=notes))

    await db.flush()

    # Attempt auto-resolution
    resolution = await _try_resolve(proposal, db)
    return {"message": "Vote recorded.", "resolution": resolution}


async def _try_resolve(proposal: QuestProposal, db: AsyncSession) -> str | None:
    """Check if quorum is met and resolve the proposal automatically."""
    from sqlalchemy import func

    # Count active guild members
    count_result = await db.execute(
        select(func.count()).where(GuildMember.guild_id == proposal.guild_id, GuildMember.is_active == True)
    )
    total_members = count_result.scalar() or 1

    # Get all votes
    result = await db.execute(
        select(ProposalVote).where(ProposalVote.proposal_id == proposal.id)
    )
    votes = result.scalars().all()
    vote_values = [v.vote.value for v in votes]

    resolution = resolve_proposal(total_members, vote_values)

    if resolution == "approved":
        await _approve_proposal(proposal, db)
    elif resolution == "rejected":
        await db.execute(
            update(QuestProposal).where(QuestProposal.id == proposal.id).values(
                status=ProposalStatusEnum.rejected,
                resolved_at=datetime.now(timezone.utc),
            )
        )
        # Notify proposer
        result = await db.execute(select(User).where(User.id == proposal.proposed_by))
        proposer = result.scalar_one_or_none()
        if proposer:
            quest_data = json.loads(proposal.proposed_data)
            from app.services.notification_service import notify_proposal_resolved
            await notify_proposal_resolved(proposer.id, quest_data.get("title", ""), False, db)

    return resolution if resolution != "needs_gm" else None


async def _approve_proposal(proposal: QuestProposal, db: AsyncSession) -> None:
    """Approve a proposal: create the QuestTemplate and first instance."""
    quest_data = json.loads(proposal.proposed_data)

    from app.models.quest import QuestTypeEnum, QuestCategoryEnum
    template = QuestTemplate(
        guild_id=proposal.guild_id,
        proposed_by=proposal.proposed_by,
        title=quest_data["title"],
        description=quest_data["description"],
        quest_type=QuestTypeEnum(quest_data["quest_type"]),
        category=QuestCategoryEnum(quest_data["category"]),
        category_custom_label=quest_data.get("category_custom_label"),
        point_worth=quest_data["point_worth"],
        xp_worth=quest_data["xp_worth"],
        start_at=datetime.fromisoformat(quest_data["start_at"]),
        deadline_at=datetime.fromisoformat(quest_data["deadline_at"]) if quest_data.get("deadline_at") else None,
        winner_point_reward=quest_data.get("winner_point_reward"),
        runner_up_point_reward=quest_data.get("runner_up_point_reward"),
        has_collective_deadline=quest_data.get("has_collective_deadline", False),
        collective_deadline_at=datetime.fromisoformat(quest_data["collective_deadline_at"]) if quest_data.get("collective_deadline_at") else None,
        status=QuestStatusEnum.active,
    )
    db.add(template)
    await db.flush()

    # Update proposal
    await db.execute(
        update(QuestProposal).where(QuestProposal.id == proposal.id).values(
            status=ProposalStatusEnum.approved,
            template_id=template.id,
            resolved_at=datetime.now(timezone.utc),
        )
    )

    # Create first instance immediately (AD-03)
    await _create_first_instance(template, db)

    # Create side quest if present
    if quest_data.get("side_quest"):
        sq = quest_data["side_quest"]
        from app.models.quest import SideQuest
        unlocks_at = template.start_at + timedelta(hours=sq["unlock_hour_offset"])
        db.add(SideQuest(
            parent_template_id=template.id,
            title=sq["title"],
            description=sq["description"],
            point_worth=sq["point_worth"],
            xp_worth=sq["xp_worth"],
            unlock_hour_offset=sq["unlock_hour_offset"],
            unlocks_at=unlocks_at,
        ))

    # Create add-on quest if present
    if quest_data.get("addon_quest"):
        aq = quest_data["addon_quest"]
        from app.models.quest import AddonQuest
        db.add(AddonQuest(
            parent_template_id=template.id,
            title=aq["title"],
            description=aq["description"],
            point_worth=aq["point_worth"],
            xp_worth=aq["xp_worth"],
            addon_deadline=datetime.fromisoformat(aq["addon_deadline"]),
            status="active",
        ))

    # Notify proposer
    result = await db.execute(select(User).where(User.id == proposal.proposed_by))
    proposer = result.scalar_one_or_none()
    if proposer:
        from app.services.notification_service import notify_proposal_resolved
        await notify_proposal_resolved(proposer.id, template.title, True, db)
        # Badge: first approved proposal
        from app.services.badge_service import _award_badge_if_eligible
        from app.services.notification_service import notify_badge_earned
        badge_name = await _award_badge_if_eligible(proposer.id, "forge_master", db)
        if badge_name:
            await notify_badge_earned(proposer.id, badge_name, db)


async def _create_first_instance(template: QuestTemplate, db: AsyncSession) -> None:
    """Create the first QuestInstance for a newly approved template (AD-03)."""
    from app.models.quest import QuestInstance, QuestTypeEnum
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    start = max(template.start_at, now)

    if template.quest_type == QuestTypeEnum.daily:
        # Ends at 23:59:59 of the start day in UTC (precise per-user timezone handled per completion check)
        from datetime import timedelta
        period_end = template.deadline_at or (start.replace(hour=23, minute=59, second=59))
    elif template.quest_type == QuestTypeEnum.weekly:
        from app.utils.timezone import week_start_sunday, week_end_saturday
        week_s = week_start_sunday(start.date())
        week_e = week_end_saturday(week_s)
        from datetime import datetime as dt
        period_end = template.deadline_at or datetime(week_e.year, week_e.month, week_e.day, 23, 59, 59, tzinfo=timezone.utc)
    else:
        period_end = template.deadline_at or (start + timedelta(days=30))

    db.add(QuestInstance(
        template_id=template.id,
        period_start=start,
        period_end=period_end,
        status=QuestStatusEnum.active,
    ))
