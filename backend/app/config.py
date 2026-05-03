"""
backend/app/config.py

Application settings loaded from environment variables.
Uses pydantic-settings for validation and type safety.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # -------------------------------------------------------------------------
    # Redis
    # -------------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"

    # -------------------------------------------------------------------------
    # Auth / Sessions
    # -------------------------------------------------------------------------
    secret_key: str
    session_ttl_days: int = 30

    # -------------------------------------------------------------------------
    # Email (Resend)
    # -------------------------------------------------------------------------
    resend_api_key: str = ""
    email_from: str = "noreply@questapp.io"
    password_reset_expiry_minutes: int = 30

    # -------------------------------------------------------------------------
    # Cloudinary
    # -------------------------------------------------------------------------
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    cloudinary_upload_folder: str = "quest-app/avatars"

    # -------------------------------------------------------------------------
    # App
    # -------------------------------------------------------------------------
    environment: str = "development"
    frontend_url: str = "http://localhost:5173"
    allowed_origins: str = "http://localhost:5173"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def session_ttl_seconds(self) -> int:
        return self.session_ttl_days * 86400


@lru_cache
def get_settings() -> Settings:
    return Settings()
