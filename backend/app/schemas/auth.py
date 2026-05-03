"""
backend/app/schemas/auth.py
"""

from pydantic import BaseModel, EmailStr, field_validator
import re


class RegisterRequest(BaseModel):
    full_name: str
    player_name: str
    email: EmailStr
    password: str
    password_hint: str
    timezone: str

    @field_validator("player_name")
    @classmethod
    def validate_player_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", v):
            raise ValueError("Player name must be 3–20 alphanumeric characters or underscores.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be empty.")
        return v.strip()


class LoginRequest(BaseModel):
    player_name: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


class PlayerNameAvailabilityResponse(BaseModel):
    player_name: str
    available: bool


class LoginResponse(BaseModel):
    message: str
    user_id: str
    player_name: str
