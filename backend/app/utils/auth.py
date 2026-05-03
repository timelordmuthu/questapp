"""
backend/app/utils/auth.py

Session token generation, hashing, and password utilities.
Architecture decision AD-01: opaque tokens in Redis, not JWTs.
"""

import hashlib
import secrets

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against the bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def generate_raw_token() -> str:
    """Generate a cryptographically random 32-byte hex token (64 chars)."""
    return secrets.token_hex(32)


def hash_token(raw_token: str) -> str:
    """SHA-256 hash of the raw token — stored in DB and Redis."""
    return hashlib.sha256(raw_token.encode()).hexdigest()
