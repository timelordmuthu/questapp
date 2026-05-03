"""
backend/app/utils/trade.py

Trade validation logic from TECH_STACK.md Section 5.
"""

import math


def validate_trade(
    sender_points: int,
    amount_sent: int,
    daily_sent_today: int,
) -> dict:
    """
    Validate a trade request.

    Rules:
    - amount_sent must be > 0
    - sender must retain at least 50 points after sending
    - daily cap = 20% of current points; cannot exceed it
    - tax = max(1, floor(sent × 0.10))
    - received = floor(sent × 0.90)

    Returns:
        {
            "valid": bool,
            "errors": list[str],
            "tax": int,
            "received": int,
        }
    """
    daily_cap = math.floor(sender_points * 0.20)
    tax = max(1, math.floor(amount_sent * 0.10))
    received = math.floor(amount_sent * 0.90)

    errors: list[str] = []

    if amount_sent <= 0:
        errors.append("Amount must be positive.")
    if sender_points - amount_sent < 50:
        errors.append("Sender must retain at least 50 points after the trade.")
    if daily_sent_today + amount_sent > daily_cap:
        remaining = max(0, daily_cap - daily_sent_today)
        errors.append(
            f"Daily trade cap exceeded. You can send at most {remaining} more points today."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "tax": tax,
        "received": received,
    }
