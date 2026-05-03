"""
backend/app/models/level.py

Level title definitions — static seed data.
"""

import uuid

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LevelTitle(Base):
    __tablename__ = "level_titles"
    __table_args__ = (UniqueConstraint("level_number", name="uq_level_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)

    @classmethod
    def get_title_for_level(cls, level: int) -> str:
        """Default title mapping — override with DB seed data."""
        titles = {
            1: "Initiate",
            2: "Novice",
            3: "Apprentice",
            4: "Journeyman",
            5: "Adept",
            6: "Skilled",
            7: "Expert",
            8: "Veteran",
            9: "Elite",
            10: "Master",
            15: "Grand Master",
            20: "Legend",
            30: "Mythic",
            50: "Transcendent",
        }
        # Find the highest matching tier
        matched = 1
        for lvl in sorted(titles.keys()):
            if level >= lvl:
                matched = lvl
        return titles[matched]
