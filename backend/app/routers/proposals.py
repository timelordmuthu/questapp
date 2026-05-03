"""
backend/app/routers/proposals.py
"""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.proposal import QuestProposal, ProposalStatusEnum, ProposalVote
from app.models.user import User
from app.schemas.guild import ProposalVoteRequest
from app.schemas.quest import QuestCreateRequest
from app.services.proposal_service import cast_vote, create_proposal

router = APIRouter()


@router.post("/guilds/{guild_id}/proposals", status_code=201)
async def submit_proposal(
    guild_id: uuid.UUID,
    data: QuestCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    proposal = await create_proposal(guild_id, data, current_user, db)
    return {"proposal_id": str(proposal.id), "voting_closes_at": proposal.voting_closes_at}


@router.get("/guilds/{guild_id}/proposals")
async def list_proposals(
    guild_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QuestProposal)
        .where(QuestProposal.guild_id == guild_id, QuestProposal.status == ProposalStatusEnum.pending)
        .order_by(QuestProposal.voting_closes_at.asc())
    )
    proposals = result.scalars().all()
    out = []
    for p in proposals:
        import json
        vote_result = await db.execute(select(ProposalVote).where(ProposalVote.proposal_id == p.id))
        votes = vote_result.scalars().all()
        out.append({
            "id": p.id,
            "proposed_by": p.proposed_by,
            "proposal_type": p.proposal_type.value,
            "proposed_data": json.loads(p.proposed_data),
            "voting_closes_at": p.voting_closes_at,
            "vote_count": len(votes),
            "user_voted": any(str(v.user_id) == str(current_user.id) for v in votes),
        })
    return out


@router.post("/proposals/{proposal_id}/vote")
async def vote_on_proposal(
    proposal_id: uuid.UUID,
    data: ProposalVoteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await cast_vote(proposal_id, data.vote, data.notes, current_user, db)
