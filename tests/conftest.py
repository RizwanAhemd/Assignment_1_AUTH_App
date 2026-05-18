import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
import asyncpg
from httpx import AsyncClient, ASGITransport
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from pydantic import PostgresDsn
from src.core.config import settings
from src.db.base import Base
from src.db.connection import get_db, get_redis
from src.main import app


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, name: str) -> str | None:
        return self.store.get(name)

    async def setex(self, name: str, time: int, value: str) -> None:
        self.store[name] = value

    async def flushdb(self) -> None:
        self.store.clear()

    async def close(self) -> None:
        return


# Config alternative async test connections
TEST_DATABASE_URL = str(
    PostgresDsn.build(
        scheme="postgresql+asyncpg",
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        path="test_core_auth",
    )
)
TEST_REDIS_URL = "redis://localhost:6379/1"


async def ensure_test_db_exists() -> None:
    admin_url = str(
        PostgresDsn.build(
            scheme="postgresql",
            username=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            path="postgres",
        )
    )
    conn = await asyncpg.connect(dsn=admin_url)
    try:
        await conn.execute("CREATE DATABASE test_core_auth")
    except asyncpg.DuplicateDatabaseError:
        pass
    finally:
        await conn.close()


test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=pool.NullPool)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_test_db():
    await ensure_test_db_exists()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture()
async def test_redis() -> AsyncGenerator[FakeRedis, None]:
    client = FakeRedis()
    yield client
    await client.flushdb()
    await client.close()


@pytest_asyncio.fixture()
async def client(
    db_session: AsyncSession, test_redis: FakeRedis
) -> AsyncGenerator[AsyncClient, None]:
    # Override dependencies with async generator functions to match FastAPI expectations
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield test_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
