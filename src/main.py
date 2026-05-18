from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import from_url
from src.api.routes import router as api_router
from src.core.config import settings
from src.db import connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Context
    connection.redis_client = from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    yield
    # Shutdown Context
    await connection.redis_client.close()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan, version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
