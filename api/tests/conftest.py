"""Pytest fixtures."""

import os
from collections.abc import AsyncGenerator

os.environ["ENVIRONMENT"] = "test"

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base, get_session, reset_db
from app.core.redis import reset_redis_client
from app.main import app


@pytest.fixture(scope="session")
async def test_engine():
    url = settings.database_url or ""
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
    reset_db()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def fake_redis():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    reset_redis_client(client)
    yield client
    await client.aclose()
    reset_redis_client(None)


@pytest.fixture
async def client(
    test_engine, test_session: AsyncSession, fake_redis
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


async def _capture_magic_token(email: str) -> str:
    """Inspect fake redis to pull the most recent token hash for this email. Tests drive
    the magic-link flow by calling /request, then extracting the raw token from the dev
    logger is fragile; we instead call the service directly in tests.
    """
    raise NotImplementedError("Use sign_in helper instead")


@pytest.fixture
async def sign_in(client: AsyncClient):
    """Returns an async function that signs in a fresh user via the magic-link service
    and sets cookies on the client. Returns (user_email, cookies_dict).
    """
    from app.auth.magic_link.service import create_magic_link

    async def _sign_in(email: str = "ethan@example.com", name: str = "Ethan Veres") -> dict:
        token = await create_magic_link(email=email, name=name)
        response = await client.post(
            "/api/v1/auth/magic-link/verify", json={"token": token}
        )
        assert response.status_code == 200, response.text
        return dict(response.cookies)

    return _sign_in
