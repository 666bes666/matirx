import asyncio
import sys
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "backend"))

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import hash_password
from app.main import app
from app.models.base import Base
from app.models.department import Department
from app.models.enums import UserRole
from app.models.user import User

TEST_DB_URL = settings.DATABASE_URL

test_engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(scope="session", autouse=True)
def setup_schema():
    async def _run():
        engine = create_async_engine(TEST_DB_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.flushdb()
        await r.aclose()

    asyncio.run(_run())
    yield

    async def _teardown():
        engine = create_async_engine(TEST_DB_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(_teardown())


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    yield r
    await r.aclose()


@pytest_asyncio.fixture
async def client(db: AsyncSession, redis_client: aioredis.Redis) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db

    async def override_get_redis():
        yield redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def department(db: AsyncSession) -> Department:
    dept = Department(name=f"Test Dept {uuid.uuid4().hex[:8]}", sort_order=1)
    db.add(dept)
    await db.flush()
    return dept


@pytest_asyncio.fixture
async def active_user(db: AsyncSession, department: Department) -> User:
    user = User(
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPass1"),
        first_name="Test",
        last_name="User",
        role=UserRole.EMPLOYEE,
        department_id=department.id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    user = User(
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("AdminPass1"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def inactive_user(db: AsyncSession) -> User:
    user = User(
        email=f"inactive_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPass1"),
        first_name="Inactive",
        last_name="User",
        role=UserRole.EMPLOYEE,
        is_active=False,
    )
    db.add(user)
    await db.flush()
    return user


async def get_auth_headers(client: AsyncClient, email: str, password: str) -> dict:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
