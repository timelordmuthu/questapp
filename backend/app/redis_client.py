"""
backend/app/redis_client.py

Async Redis client singleton.
Key conventions (from architecture_decisions.md AD-07):

  sessions:{token_hash}                   TTL: 30 days rolling
  rate_limit:login:{ip_address}           TTL: 15 minutes
  daily_trade_cap:{user_id}:{YYYY-MM-DD}  TTL: expires at end of UTC day
  notif_unread:{user_id}                  TTL: 60 seconds
  quest_feed:{user_id}                    TTL: 30 seconds
"""

import redis.asyncio as aioredis

from app.config import get_settings

settings = get_settings()

# Module-level client — created once on startup, shared across requests.
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return the shared Redis client (initialises lazily)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection on app shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


# ---------------------------------------------------------------------------
# Key builders — single source of truth for key naming
# ---------------------------------------------------------------------------
def session_key(token_hash: str) -> str:
    return f"sessions:{token_hash}"


def rate_limit_key(ip: str) -> str:
    return f"rate_limit:login:{ip}"


def trade_cap_key(user_id: str, date_str: str) -> str:
    """date_str = YYYY-MM-DD in UTC"""
    return f"daily_trade_cap:{user_id}:{date_str}"


def notif_unread_key(user_id: str) -> str:
    return f"notif_unread:{user_id}"


def quest_feed_key(user_id: str) -> str:
    return f"quest_feed:{user_id}"
