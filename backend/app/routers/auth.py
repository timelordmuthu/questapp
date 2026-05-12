"""
backend/app/routers/auth.py
"""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    PlayerNameAvailabilityResponse,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.services import auth_service

router = APIRouter()


@router.post("/register", status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(data, db)
    return {"message": "Registration successful.", "player_name": user.player_name}


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host
    return await auth_service.login_user(data, response, db, client_ip)


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    raw_token = request.cookies.get("session_token", "")
    await auth_service.logout_user(raw_token, db)
    response.delete_cookie("session_token", httponly=True, secure=True, samesite="none")


@router.post("/forgot-password", status_code=204)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.request_password_reset(str(data.email), db)


@router.post("/reset-password", status_code=204)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.reset_password(data.token, data.new_password, db)


@router.get("/check-player-name/{player_name}", response_model=PlayerNameAvailabilityResponse)
async def check_player_name(player_name: str, db: AsyncSession = Depends(get_db)):
    available = await auth_service.check_player_name_available(player_name, db)
    return {"player_name": player_name, "available": available}
