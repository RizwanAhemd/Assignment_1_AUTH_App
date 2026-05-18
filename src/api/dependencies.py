from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.security import decode_token
from src.db.connection import get_db, get_redis
from src.models.user import User
from src.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check Blacklist Status
    is_blacklisted = False
    try:
        if await redis.get(f"blacklist:{token}"):
            is_blacklisted = True
    except Exception as e:
        # If Redis is down, we log it but continue (JWT is still valid cryptographically)
        print(f"Warning: Redis check failed ({e}). Proceeding with JWT validation only.")
        
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked. Please login again."
        )

    try:
        payload = decode_token(token, "access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = await UserRepository(db).get_by_id(int(user_id))
    if user is None:
        raise credentials_exception
    return user