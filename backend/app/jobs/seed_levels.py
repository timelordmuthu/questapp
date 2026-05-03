"""
backend/app/jobs/seed_levels.py

One-time level title seed.
Run: python -m app.jobs.seed_levels
"""

import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.database import AsyncSessionLocal
from app.models.level import LevelTitle

LEVELS = [
    (1,  "Initiate"),
    (2,  "Novice"),
    (3,  "Apprentice"),
    (4,  "Journeyman"),
    (5,  "Adept"),
    (6,  "Skilled"),
    (7,  "Expert"),
    (8,  "Veteran"),
    (9,  "Elite"),
    (10, "Master"),
    (15, "Grand Master"),
    (20, "Legend"),
    (30, "Mythic"),
    (50, "Transcendent"),
]


async def seed():
    async with AsyncSessionLocal() as db:
        for lvl, title in LEVELS:
            stmt = pg_insert(LevelTitle).values(
                level_number=lvl,
                title=title,
            ).on_conflict_do_update(
                index_elements=["level_number"],
                set_={"title": title},
            )
            await db.execute(stmt)
        await db.commit()
        print(f"✓ Seeded {len(LEVELS)} level titles.")


if __name__ == "__main__":
    asyncio.run(seed())
