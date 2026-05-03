"""
backend/app/utils/xp.py

XP formula, level calculation, streak multiplier.
All formulas from TECH_STACK.md Section 5.
"""

import math


def xp_for_level(n: int) -> int:
    """XP required to advance FROM level n-1 TO level n."""
    return round(100 * (n ** 1.8))


def level_from_total_xp(total_xp: int) -> int:
    """Binary search current level given total XP."""
    level = 1
    cumulative = 0
    while True:
        needed = xp_for_level(level)
        if cumulative + needed > total_xp:
            return level - 1 if level > 1 else 1
        cumulative += needed
        level += 1


def xp_to_next_level(total_xp: int) -> int:
    """How much more XP until the next level."""
    current = level_from_total_xp(total_xp)
    cumulative = sum(xp_for_level(l) for l in range(1, current + 1))
    needed_for_next = xp_for_level(current + 1)
    xp_into_current = total_xp - cumulative
    return needed_for_next - xp_into_current


def get_streak_multiplier(streak_count: int) -> float:
    """
    Streak XP multiplier tiers:
      0         → ×1.0 (no boost)
      1–3       → ×1.2
      4–6       → ×1.5
      7–13      → ×2.0
      14–29     → ×2.5
      30+       → ×3.0 (hard cap)
    """
    if streak_count <= 0:
        return 1.0
    elif streak_count <= 3:
        return 1.2
    elif streak_count <= 6:
        return 1.5
    elif streak_count <= 13:
        return 2.0
    elif streak_count <= 29:
        return 2.5
    else:
        return 3.0


def apply_xp(base_xp: int, quest_type: str, daily_streak: int, weekly_streak: int) -> int:
    """
    Apply streak multiplier based on quest type.
    Rules:
      - daily   → daily_streak multiplier
      - weekly  → weekly_streak multiplier
      - all others (occasional, competition, group, side, addon) → ×1.0
    """
    if quest_type == "daily":
        multiplier = get_streak_multiplier(daily_streak)
    elif quest_type == "weekly":
        multiplier = get_streak_multiplier(weekly_streak)
    else:
        multiplier = 1.0
    return math.floor(base_xp * multiplier)


def get_level_title(level: int) -> str:
    """Return the display title for a given level."""
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
    matched_title = "Initiate"
    for lvl in sorted(titles.keys()):
        if level >= lvl:
            matched_title = titles[lvl]
    return matched_title
