-- =============================================================================
-- backend/app/jobs/seed_badges.py equivalent — run once after alembic upgrade head
-- Or paste into psql directly.
-- =============================================================================
-- 
-- Run via: python -m app.jobs.seed_badges
-- =============================================================================

"""
backend/app/jobs/seed_badges.py

One-time badge seed script.
Run: python -m app.jobs.seed_badges
"""

import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.database import AsyncSessionLocal
from app.models.badge import Badge, BadgeCategoryEnum

BADGES = [
    # Quest badges
    dict(badge_key="first_flame",     name="First Flame",       description="Complete your very first quest.",
         hint="Complete 1 quest.",            category="quest",   icon_symbol="🕯"),
    dict(badge_key="ten_trials",      name="Ten Trials",         description="Complete 10 quests across any source.",
         hint="Complete 10 quests.",          category="quest",   icon_symbol="⚔"),
    dict(badge_key="century_mark",    name="Century Mark",       description="Complete 100 quests.",
         hint="Complete 100 quests.",         category="quest",   icon_symbol="💯"),
    dict(badge_key="the_relentless",  name="The Relentless",     description="Complete 500 quests.",
         hint="Complete 500 quests.",         category="quest",   icon_symbol="🔱"),
    dict(badge_key="forge_master",    name="Forge Master",       description="Have a guild quest proposal approved.",
         hint="Propose a quest that gets approved.", category="quest", icon_symbol="⚒"),
    dict(badge_key="warchief",        name="Warchief",           description="Win a Competition Quest.",
         hint="Win a Competition Quest.",     category="quest",   icon_symbol="👑"),

    # Streak badges
    dict(badge_key="kindled",         name="Kindled",            description="Maintain a 3-day daily streak.",
         hint="Reach a 3-day streak.",        category="streak",  icon_symbol="🔥"),
    dict(badge_key="burning_path",    name="Burning Path",       description="Maintain a 7-day daily streak.",
         hint="Reach a 7-day streak.",        category="streak",  icon_symbol="🌋"),
    dict(badge_key="eternal_flame",   name="Eternal Flame",      description="Maintain a 30-day daily streak.",
         hint="Reach a 30-day streak.",       category="streak",  icon_symbol="☀"),
    dict(badge_key="weekly_ritual",   name="Weekly Ritual",      description="Maintain a 4-week weekly streak.",
         hint="Reach a 4-week streak.",       category="streak",  icon_symbol="⚡"),
    dict(badge_key="ancient_rite",    name="Ancient Rite",       description="Maintain a 12-week weekly streak.",
         hint="Reach a 12-week streak.",      category="streak",  icon_symbol="🌙"),

    # Level badges
    dict(badge_key="awakened",        name="Awakened",           description="Reach Level 5.",
         hint="Reach Level 5.",               category="level",   icon_symbol="✨"),
    dict(badge_key="ascended",        name="Ascended",           description="Reach Level 10.",
         hint="Reach Level 10.",              category="level",   icon_symbol="🌟"),
    dict(badge_key="transcendent",    name="Transcendent",       description="Reach Level 20.",
         hint="Reach Level 20.",              category="level",   icon_symbol="💫"),
    dict(badge_key="the_undying",     name="The Undying",        description="Reach Level 50.",
         hint="Reach Level 50.",              category="level",   icon_symbol="♾"),

    # Social badges
    dict(badge_key="bound_by_oath",   name="Bound by Oath",      description="Join your first Guild.",
         hint="Join a Guild.",                category="social",  icon_symbol="🛡"),
    dict(badge_key="founding_rune",   name="Founding Rune",      description="Create a Guild.",
         hint="Create a Guild.",              category="social",  icon_symbol="📜"),
    dict(badge_key="guild_master",    name="Guild Master",        description="Hold the title of Guild Master.",
         hint="Become a Guild Master.",       category="social",  icon_symbol="👑"),

    # Trade badges
    dict(badge_key="generous_soul",   name="Generous Soul",       description="Send your first trade.",
         hint="Send 1 trade.",                category="trade",   icon_symbol="💰"),
    dict(badge_key="tithe_of_ancients",name="Tithe of Ancients", description="Send 10 trades.",
         hint="Send 10 trades.",              category="trade",   icon_symbol="💎"),

    # Sanctum badges
    dict(badge_key="lone_wanderer",   name="Lone Wanderer",       description="Complete 10 Sanctum quests.",
         hint="Complete 10 Sanctum quests.",  category="sanctum", icon_symbol="🕯"),
    dict(badge_key="inner_sanctum",   name="Inner Sanctum",       description="Complete 50 Sanctum quests.",
         hint="Complete 50 Sanctum quests.",  category="sanctum", icon_symbol="🔮"),
]


async def seed():
    async with AsyncSessionLocal() as db:
        for b in BADGES:
            stmt = pg_insert(Badge).values(
                badge_key=b["badge_key"],
                name=b["name"],
                description=b["description"],
                hint=b["hint"],
                category=BadgeCategoryEnum(b["category"]),
                icon_symbol=b["icon_symbol"],
            ).on_conflict_do_update(
                index_elements=["badge_key"],
                set_={
                    "name": b["name"],
                    "description": b["description"],
                    "hint": b["hint"],
                    "icon_symbol": b["icon_symbol"],
                }
            )
            await db.execute(stmt)
        await db.commit()
        print(f"✓ Seeded {len(BADGES)} badges.")


if __name__ == "__main__":
    asyncio.run(seed())
