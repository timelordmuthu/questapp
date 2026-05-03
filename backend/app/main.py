"""
backend/app/main.py

FastAPI application entry point.
Registers all routers, CORS middleware, lifespan events.
"""

from contextlib import asynccontextmanager

import cloudinary
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.redis_client import close_redis, get_redis
from app.routers import (
    auth,
    guilds,
    leaderboard,
    notifications,
    proposals,
    quests,
    sanctum,
    trades,
    users,
)

settings = get_settings()


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await get_redis()  # warm the Redis connection
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    yield
    # Shutdown
    await close_redis()


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Quest App API",
    description="Magical dark-themed group challenge platform.",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(sanctum.router, prefix="/sanctum", tags=["Sanctum"])
app.include_router(guilds.router, prefix="/guilds", tags=["Guilds"])
app.include_router(proposals.router, prefix="/proposals", tags=["Proposals"])
app.include_router(quests.router, prefix="/quests", tags=["Quests"])
app.include_router(trades.router, prefix="/trades", tags=["Trades"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboard"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "environment": settings.environment}
