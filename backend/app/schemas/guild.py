"""
backend/app/schemas/guild.py
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class GuildCreateRequest(BaseModel):
    name: str


class GuildJoinRequest(BaseModel):
    sigil_code: str


class GuildUpdateRequest(BaseModel):
    name: str | None = None
    max_points_per_quest: int | None = None
    max_xp_per_quest: int | None = None


class MemberResponse(BaseModel):
    user_id: uuid.UUID
    player_name: str
    full_name: str
    avatar_url: str | None
    current_level: int
    level_title: str
    joined_at: datetime
    last_active_at: datetime | None
    is_guild_master: bool

    model_config = {"from_attributes": True}


class GuildResponse(BaseModel):
    id: uuid.UUID
    name: str
    sigil_code: str
    guild_master_id: uuid.UUID
    max_points_per_quest: int
    max_xp_per_quest: int
    member_count: int
    members: list[MemberResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class TransferGuildMasterRequest(BaseModel):
    new_gm_user_id: uuid.UUID


"""
backend/app/schemas/proposal.py
"""


class ProposalVoteRequest(BaseModel):
    vote: str  # accept | decline | suggest_changes
    notes: str | None = None


class ProposalResponse(BaseModel):
    id: uuid.UUID
    guild_id: uuid.UUID
    proposed_by_player_name: str
    proposal_type: str
    status: str
    proposed_data: dict
    voting_closes_at: datetime
    votes: list[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


"""
backend/app/schemas/trade.py
"""


class TradeRequest(BaseModel):
    receiver_player_name: str
    amount: int
    guild_id: uuid.UUID


class TradeValidateRequest(BaseModel):
    amount: int
    guild_id: uuid.UUID


class TradeValidateResponse(BaseModel):
    valid: bool
    errors: list[str]
    tax: int
    received: int
    daily_cap: int
    daily_sent_today: int


class TradeResponse(BaseModel):
    id: uuid.UUID
    sender_player_name: str
    receiver_player_name: str
    amount_sent: int
    amount_received: int
    tax_amount: int
    created_at: datetime

    model_config = {"from_attributes": True}


"""
backend/app/schemas/notification.py
"""


class NotificationResponse(BaseModel):
    id: uuid.UUID
    category: str
    title: str
    body: str
    link: str | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationSettingUpdate(BaseModel):
    category: str
    enabled: bool


"""
backend/app/schemas/leaderboard.py
"""


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    player_name: str
    full_name: str
    avatar_url: str | None
    current_level: int
    level_title: str
    points: int
    is_current_user: bool

    model_config = {"from_attributes": True}


class LeaderboardResponse(BaseModel):
    guild_id: uuid.UUID
    type: str  # all_time | seasonal
    season_year: int | None
    season_month: int | None
    entries: list[LeaderboardEntry]
