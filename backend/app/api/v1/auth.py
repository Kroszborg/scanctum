from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_async_session),
):
    service = AuthService(db)
    return await service.login(body.email, body.password)


@router.post("/signup", response_model=LoginResponse)
async def signup(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """Public signup. First user becomes admin, others become analyst."""
    service = AuthService(db)
    user = await service.register_public(body)
    return await service.login(user.email, body.password)


@router.post("/register", response_model=UserResponse)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role("admin")),
):
    """Admin-only: create another user."""
    service = AuthService(db)
    return await service.register(body)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
