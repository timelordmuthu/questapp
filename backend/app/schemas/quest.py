"""
backend/app/schemas/quest.py
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.quest import QuestCategoryEnum, QuestTypeEnum


class SideQuestIn(BaseModel):
    title: str
    description: str
    point_worth: int
    xp_worth: int
    unlock_hour_offset: int  # hours after parent start


class AddonQuestIn(BaseModel):
    title: str
    description: str
    point_worth: int
    xp_worth: int
    addon_deadline: datetime


class QuestCreateRequest(BaseModel):
    title: str
    description: str
    quest_type: QuestTypeEnum
    category: QuestCategoryEnum
    category_custom_label: str | None = None  # if category == 'other'
    point_worth: int
    xp_worth: int
    start_at: datetime
    deadline_at: datetime | None = None
    # Competition-specific
    winner_point_reward: int | None = None
    runner_up_point_reward: int | None = None
    # Group-specific
    has_collective_deadline: bool = False
    collective_deadline_at: datetime | None = None
    # Optional sub-quests
    side_quest: SideQuestIn | None = None
    addon_quest: AddonQuestIn | None = None

    @field_validator("category_custom_label")
    @classmethod
    def validate_custom_label(cls, v: str | None) -> str | None:
        if v and len(v) > 30:
            raise ValueError("Custom category label max 30 characters.")
        return v


class QuestCardResponse(BaseModel):
    instance_id: uuid.UUID
    template_id: uuid.UUID
    title: str
    quest_type: str
    category: str
    category_custom_label: str | None
    source: str  # "Sanctum" or guild name
    point_worth: int
    xp_worth: int
    period_start: datetime
    period_end: datetime
    completion_status: str  # pending / done / missed
    points_earned: int
    xp_earned: int
    # Group quest progress
    group_total: int | None
    group_done: int | None
    # Competition
    is_competition: bool
    voting_open: bool | None

    model_config = {"from_attributes": True}


class MarkDoneResponse(BaseModel):
    message: str
    points_earned: int
    xp_earned: int
    new_total_points: int
    new_total_xp: int
    new_level: int
    level_up: bool
    streak_multiplier: float
    badges_earned: list[str]
