"""
backend/app/schemas/user.py
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class BadgeOut(BaseModel):
    badge_key: str
    name: str
    description: str
    hint: str
    category: str
    icon_symbol: str
    earned_at: datetime | None = None
    is_unlocked: bool = False

    model_config = {"from_attributes": True}


class WallOfGloryItem(BaseModel):
    completion_id: uuid.UUID
    quest_title: str
    quest_type: str
    points_earned: int
    xp_earned: int
    completed_at: datetime
    pin_order: int

    model_config = {"from_attributes": True}


class PublicProfileResponse(BaseModel):
    id: uuid.UUID
    player_name: str
    full_name: str
    avatar_url: str | None
    current_level: int
    level_title: str
    total_xp: int
    xp_to_next_level: int
    daily_streak: int
    weekly_streak: int
    badges: list[BadgeOut]
    wall_of_glory: list[WallOfGloryItem]
    guild_names: list[str]

    model_config = {"from_attributes": True}


class OwnProfileResponse(PublicProfileResponse):
    total_points: int
    email: str
    timezone: str
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    timezone: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class PinQuestRequest(BaseModel):
    completion_id: uuid.UUID
    pin_order: int  # 1, 2, or 3


class CompletedQuestHistoryItem(BaseModel):
    completion_id: uuid.UUID
    quest_title: str
    quest_type: str
    category: str
    source: str  # "Sanctum" or guild name
    points_earned: int
    xp_earned: int
    completed_at: datetime | None
    status: str  # done / missed
    is_pinned: bool

    model_config = {"from_attributes": True}


class CompletedQuestHistoryResponse(BaseModel):
    items: list[CompletedQuestHistoryItem]
    total: int
    page: int
    page_size: int
