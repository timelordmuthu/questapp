"""
backend/app/services/auth_service.py

Registration, login, logout, password reset.
Session strategy: AD-01 (opaque tokens in Redis).
"""

import json
import uuid
from datetime import datetime, timedelta, timezone

import resend
from fastapi import HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.notification import NotificationSetting, NotificationCategoryEnum
from app.models.sanctum import Sanctum
from app.models.user import PasswordResetToken, Session as DBSession, User
from app.redis_client import get_redis, rate_limit_key, session_key
from app.schemas.auth import LoginRequest, RegisterRequest
from app.utils.auth import (
    generate_raw_token,
    hash_password,
    hash_token,
    verify_password,
)

settings = get_settings()


async def register_user(data: RegisterRequest, db: AsyncSession) -> User:
    """Create a new user account + Sanctum + default notification settings."""
    # Check player_name uniqueness
    result = await db.execute(select(User).where(User.player_name == data.player_name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Player name already taken.")

    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    user = User(
        player_name=data.player_name,
        full_name=data.full_name,
        email=str(data.email),
        password_hash=hash_password(data.password),
        password_hint=data.password_hint,
        timezone=data.timezone,
    )
    db.add(user)
    await db.flush()  # get user.id

    # Auto-create Sanctum
    sanctum = Sanctum(user_id=user.id)
    db.add(sanctum)

    # Default notification settings (all enabled)
    for category in NotificationCategoryEnum:
        db.add(NotificationSetting(user_id=user.id, category=category, enabled=True))

    await db.flush()
    return user


async def login_user(
    data: LoginRequest,
    response: Response,
    db: AsyncSession,
    client_ip: str,
) -> dict:
    """Authenticate user, create session, set HttpOnly cookie."""
    redis = await get_redis()

    # Rate limiting: 10 attempts per 15 minutes per IP
    rl_key = rate_limit_key(client_ip)
    attempts = await redis.incr(rl_key)
    if attempts == 1:
        await redis.expire(rl_key, 900)  # 15 min TTL on first attempt
    if attempts > 10:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts. Try again later.")

    # Lookup user by player_name
    result = await db.execute(select(User).where(User.player_name == data.player_name))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_account",  # frontend shows "No account found" popup
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "wrong_password", "hint": user.password_hint},
        )

    # Clear rate limit on success
    await redis.delete(rl_key)

    # Create session
    raw_token = generate_raw_token()
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.session_ttl_days)

    db_session = DBSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(db_session)

    # Store in Redis
    await redis.setex(
        session_key(token_hash),
        settings.session_ttl_seconds,
        json.dumps({"user_id": str(user.id)}),
    )

    # Set HttpOnly cookie
    response.set_cookie(
        key="session_token",
        value=raw_token,
        httponly=True,
        secure=True,             # must be True for samesite=none
        samesite="none",         # ← allows cross-origin
        max_age=settings.session_ttl_seconds,
    )

    return {
        "message": "Login successful.",
        "user_id": str(user.id),
        "player_name": user.player_name,
    }


async def logout_user(raw_token: str, db: AsyncSession) -> None:
    """Invalidate session in Redis and DB."""
    if not raw_token:
        return
    token_hash = hash_token(raw_token)
    redis = await get_redis()
    await redis.delete(session_key(token_hash))
    await db.execute(
        update(DBSession).where(DBSession.token_hash == token_hash).values(expires_at=datetime.now(timezone.utc))
    )


async def request_password_reset(email: str, db: AsyncSession) -> None:
    """Send a one-time password reset email if the email is registered."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return  # Silent — don't leak whether email exists

    raw_token = generate_raw_token()
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_expiry_minutes)

    db.add(PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    await db.flush()

    reset_link = f"{settings.frontend_url}/reset-password?token={raw_token}"

    if settings.resend_api_key:
        resend.api_key = settings.resend_api_key
        resend.Emails.send({
            "from": settings.email_from,
            "to": user.email,
            "subject": "Quest App — Password Reset",
            "html": f"""
                <h2>Password Reset</h2>
                <p>Click the link below to reset your password. It expires in {settings.password_reset_expiry_minutes} minutes.</p>
                <a href="{reset_link}">{reset_link}</a>
                <p>If you didn't request this, ignore this email.</p>
            """,
        })


async def reset_password(token: str, new_password: str, db: AsyncSession) -> None:
    """Validate reset token and update password."""
    token_hash = hash_token(token)
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
            PasswordResetToken.used_at.is_(None),
        )
    )
    reset_record = result.scalar_one_or_none()
    if not reset_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token.")

    await db.execute(
        update(User).where(User.id == reset_record.user_id).values(password_hash=hash_password(new_password))
    )
    await db.execute(
        update(PasswordResetToken).where(PasswordResetToken.id == reset_record.id).values(used_at=datetime.now(timezone.utc))
    )


async def check_player_name_available(player_name: str, db: AsyncSession) -> bool:
    result = await db.execute(select(User).where(User.player_name == player_name))
    return result.scalar_one_or_none() is None
