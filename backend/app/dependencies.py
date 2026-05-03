"""
backend/app/dependencies.py

FastAPI dependencies for session validation.
AD-01: hash incoming cookie token → lookup in Redis → load user.
"""

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import Session as DBSession, User
from app.redis_client import get_redis, session_key
from app.utils.auth import hash_token

settings = get_settings()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the session cookie and return the authenticated user.
    Raises 401 if session is missing, invalid, or expired.
    """
    raw_token: str | None = request.cookies.get("session_token")
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    token_hash = hash_token(raw_token)

    # 1. Check Redis first (fast path)
    redis = await get_redis()
    session_data = await redis.get(session_key(token_hash))

    if not session_data:
        # 2. Fallback to DB (e.g. Redis was flushed)
        result = await db.execute(
            select(DBSession).where(
                DBSession.token_hash == token_hash,
                DBSession.expires_at > datetime.now(timezone.utc),
            )
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid.")

        user_id = str(db_session.user_id)

        # Re-populate Redis
        await redis.setex(
            session_key(token_hash),
            settings.session_ttl_seconds,
            json.dumps({"user_id": user_id}),
        )
    else:
        user_id = json.loads(session_data)["user_id"]

    # Rolling TTL — reset on each use
    await redis.expire(session_key(token_hash), settings.session_ttl_seconds)

    # Update DB session last_used_at and expires_at
    new_expiry = datetime.now(timezone.utc) + timedelta(days=settings.session_ttl_days)
    await db.execute(
        update(DBSession)
        .where(DBSession.token_hash == token_hash)
        .values(last_used_at=datetime.now(timezone.utc), expires_at=new_expiry)
    )

    # Load user
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    # Update last_active_at
    await db.execute(
        update(User).where(User.id == user.id).values(last_active_at=datetime.now(timezone.utc))
    )

    return user


# Alias for optional auth (returns None if not logged in)
async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None
