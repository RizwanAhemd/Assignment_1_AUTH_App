from typing import Literal
from pydantic import BaseModel


class TokenExchangeResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class StandardActionResponse(BaseModel):
    detail: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
