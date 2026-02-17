from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginResponse, RegisterRequest, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, email: str, password: str) -> LoginResponse:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("Account is disabled")

        token = create_access_token({"sub": str(user.id)})
        return LoginResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    async def register_public(self, data: RegisterRequest) -> User:
        """Public signup. First user gets role admin, others get analyst."""
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none() is not None:
            raise ConflictError("Email already registered")
        count_result = await self.db.execute(select(func.count()).select_from(User))
        is_first = (count_result.scalar() or 0) == 0
        role = "admin" if is_first else (data.role or "analyst")
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=role,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def register(self, data: RegisterRequest) -> User:
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none() is not None:
            raise ConflictError("Email already registered")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
