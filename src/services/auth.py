from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
import jwt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import settings
from src.core.security import create_token, decode_token, hash_password, verify_password
from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.user_repo = UserRepository(db)
        self.redis = redis

    async def register_user(self, user_in: UserCreate) -> User:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists.",
            )

        new_user = User(
            email=user_in.email, hashed_password=hash_password(user_in.password)
        )
        return await self.user_repo.create(new_user)

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user."
            )
        return user

    def generate_auth_tokens(self, user_id: int) -> dict:
        access_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        return {
            "access_token": create_token(user_id, access_delta, "access"),
            "refresh_token": create_token(user_id, refresh_delta, "refresh"),
            "token_type": "bearer",
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token, "refresh")
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh payload",
                )
            return self.generate_auth_tokens(int(user_id))
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

    async def blacklist_token(self, token: str, payload: dict) -> None:
        exp_timestamp = payload.get("exp")
        now = datetime.now(timezone.utc).timestamp()
        ttl = int(exp_timestamp - now)
        if ttl > 0:
            try:
                await self.redis.setex(
                    name=f"blacklist:{token}", time=ttl, value="true"
                )
            except Exception as e:
                print(f"Warning: Failed to blacklist token in Redis ({e})")
