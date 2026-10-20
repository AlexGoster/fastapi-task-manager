"""Shared test fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db() -> AsyncSession:
    async with TestSession() as session:
        yield session


@pytest.fixture(autouse=True)
async def init_db():
    app.dependency_overrides[get_db] = override_get_db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()
    app.dependency_overrides.clear()


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def token_for():
    async def create_token(client: AsyncClient, username: str = "taskuser") -> str:
        response = await client.post(
            "/auth/register",
            json={
                "username": username,
                "email": f"{username}@e.com",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        response = await client.post(
            "/auth/login",
            data={
                "username": username,
                "password": "password123",
            },
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    return create_token
