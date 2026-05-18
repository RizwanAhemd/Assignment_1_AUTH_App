from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import get_current_user, oauth2_scheme
from src.core.security import decode_token
from src.db.connection import get_db, get_redis
from src.models.user import User
from src.schemas.auth import RefreshTokenRequest, StandardActionResponse, TokenExchangeResponse
from src.schemas.user import UserCreate, UserRegistrationResponse
from src.services.auth import AuthService

router = APIRouter()

@router.post(
    "/auth/register",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED
)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)):
    auth_service = AuthService(db, redis)
    return await auth_service.register_user(user_in)

@router.post("/auth/login", response_model=TokenExchangeResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    auth_service = AuthService(db, redis)
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    return auth_service.generate_auth_tokens(user.id)

@router.post("/auth/refresh", response_model=TokenExchangeResponse)
async def refresh(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    auth_service = AuthService(db, redis)
    return await auth_service.refresh_access_token(body.refresh_token)

@router.post("/auth/logout", response_model=StandardActionResponse)
async def logout(
    token: str = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis)
):
    payload = decode_token(token, "access")
    auth_service = AuthService(None, redis)  # DB instance omitted intentionally
    await auth_service.blacklist_token(token, payload)
    return {"detail": "Successfully logged out."}

@router.get("/users/me", response_model=UserRegistrationResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user