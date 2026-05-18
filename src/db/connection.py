from typing import AsyncGenerator, Optional
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.core.config import settings

# Async SQLAlchemy Configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Async Redis Engine Client
redis_client: Optional[Redis] = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing database sessions to requests."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[Redis, None]:
    """Dependency for providing a Redis client instance."""
    global redis_client
    if redis_client is None:
        raise RuntimeError("Redis connection client has not been initialized.")
    yield redis_client
