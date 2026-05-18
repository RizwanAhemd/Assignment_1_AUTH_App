from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from passlib.context import CryptContext
from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(subject: Any, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    payload = {
        "exp": expire,
        "iat": now,
        "sub": str(subject),
        "type": token_type
    }
    
    secret = (
        settings.JWT_ACCESS_SECRET 
        if token_type == "access" 
        else settings.JWT_REFRESH_SECRET
    )
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_token(token: str, token_type: str) -> Dict[str, Any]:
    secret = (
        settings.JWT_ACCESS_SECRET 
        if token_type == "access" 
        else settings.JWT_REFRESH_SECRET
    )
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        if payload.get("type") != token_type:
            raise jwt.InvalidTokenError("Invalid token scope/type")
        return payload
    except jwt.PyJWTError:
        raise jwt.InvalidTokenError("Token parse/validation error")