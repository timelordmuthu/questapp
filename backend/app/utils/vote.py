"""
backend/app/utils/vote.py

Quorum and vote resolution logic from TECH_STACK.md Section 5.
"""

import math


def resolve_proposal(total_members: int, votes: list[str]) -> str:
    """
    Resolve a quest proposal vote.

    votes: list of 'accept' | 'decline' | 'suggest_changes'
           (suggest_changes is counted as decline for quorum purposes)

    Returns:
        'approved'  — majority accept
        'rejected'  — majority decline/suggest_changes
        'needs_gm'  — quorum not reached OR exact tie → GM casts deciding vote
    """
    quorum_required = math.ceil(total_members * 0.6)
    actual_votes = len(votes)

    if actual_votes < quorum_required:
        return "needs_gm"

    accept_count = sum(1 for v in votes if v == "accept")
    decline_count = actual_votes - accept_count  # decline + suggest_changes

    if accept_count > decline_count:
        return "approved"
    elif decline_count > accept_count:
        return "rejected"
    else:
        return "needs_gm"  # Exact tie → GM's vote counts double
