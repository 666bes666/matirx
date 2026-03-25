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
from app.models.team import Team
from app.models.user import User

TEST_DB_URL = settings.DATABASE_URL

test_engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="module", autouse=True)
def setup_schema():
    async def _create():
        engine = create_async_engine(TEST_DB_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_create())
    yield


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
async def active_user(db: AsyncSession) -> User:
    user = User(
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("UserPass1"),
        first_name="Regular",
        last_name="User",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def _get_auth_headers(client: AsyncClient, email: str, password: str) -> dict:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_departments_ok(client: AsyncClient, active_user: User):
    headers = await _get_auth_headers(client, active_user.email, "UserPass1")
    resp = await client.get("/api/v1/departments", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_department_as_admin(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    resp = await client.post(
        "/api/v1/departments",
        json={"name": f"New Dept {uuid.uuid4().hex[:8]}", "sort_order": 99},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert "name" in data


@pytest.mark.asyncio
async def test_create_department_duplicate_name(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    name = f"Dupe Dept {uuid.uuid4().hex[:8]}"
    resp1 = await client.post(
        "/api/v1/departments",
        json={"name": name, "sort_order": 10},
        headers=headers,
    )
    assert resp1.status_code == 201
    resp2 = await client.post(
        "/api/v1/departments",
        json={"name": name, "sort_order": 10},
        headers=headers,
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_get_department_by_id(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    create_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"Get Dept {uuid.uuid4().hex[:8]}", "sort_order": 5},
        headers=headers,
    )
    assert create_resp.status_code == 201
    dept_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/departments/{dept_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == dept_id


@pytest.mark.asyncio
async def test_update_department(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    create_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"Upd Dept {uuid.uuid4().hex[:8]}", "sort_order": 3},
        headers=headers,
    )
    assert create_resp.status_code == 201
    dept_id = create_resp.json()["id"]

    new_name = f"Updated {uuid.uuid4().hex[:8]}"
    resp = await client.patch(
        f"/api/v1/departments/{dept_id}",
        json={"name": new_name},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == new_name


@pytest.mark.asyncio
async def test_delete_department(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    create_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"Del Dept {uuid.uuid4().hex[:8]}", "sort_order": 20},
        headers=headers,
    )
    assert create_resp.status_code == 201
    dept_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/departments/{dept_id}", headers=headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_create_team(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    dept_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"Team Dept {uuid.uuid4().hex[:8]}", "sort_order": 7},
        headers=headers,
    )
    assert dept_resp.status_code == 201
    dept_id = dept_resp.json()["id"]

    team_resp = await client.post(
        f"/api/v1/departments/{dept_id}/teams",
        json={"name": "Alpha Team"},
        headers=headers,
    )
    assert team_resp.status_code == 201
    data = team_resp.json()
    assert "id" in data
    assert data["department_id"] == dept_id


@pytest.mark.asyncio
async def test_delete_team_not_empty(client: AsyncClient, admin_user: User, db: AsyncSession):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    dept_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"Nonempty Dept {uuid.uuid4().hex[:8]}", "sort_order": 8},
        headers=headers,
    )
    assert dept_resp.status_code == 201
    dept_id = uuid.UUID(dept_resp.json()["id"])

    team_resp = await client.post(
        f"/api/v1/departments/{dept_id}/teams",
        json={"name": "Beta Team"},
        headers=headers,
    )
    assert team_resp.status_code == 201
    team_id = uuid.UUID(team_resp.json()["id"])

    user = User(
        email=f"emp_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("EmpPass1!"),
        first_name="Emp",
        last_name="User",
        role=UserRole.EMPLOYEE,
        department_id=dept_id,
        team_id=team_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    resp = await client.delete(
        f"/api/v1/departments/{dept_id}/teams/{team_id}",
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_delete_protected_department(client: AsyncClient, admin_user: User, db: AsyncSession):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    dept = Department(name="Первая линия", description="Protected", sort_order=1)
    db.add(dept)
    await db.flush()

    resp = await client.delete(f"/api/v1/departments/{dept.id}", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_department_not_found(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    resp = await client.get(f"/api/v1/departments/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_teams(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    dept_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"ListTeam Dept {uuid.uuid4().hex[:8]}", "sort_order": 11},
        headers=headers,
    )
    assert dept_resp.status_code == 201
    dept_id = dept_resp.json()["id"]

    await client.post(
        f"/api/v1/departments/{dept_id}/teams",
        json={"name": "Team X"},
        headers=headers,
    )

    resp = await client.get(f"/api/v1/departments/{dept_id}/teams", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_team_by_id(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    dept_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"GetTeam Dept {uuid.uuid4().hex[:8]}", "sort_order": 12},
        headers=headers,
    )
    dept_id = dept_resp.json()["id"]

    team_resp = await client.post(
        f"/api/v1/departments/{dept_id}/teams",
        json={"name": "Team Y"},
        headers=headers,
    )
    team_id = team_resp.json()["id"]

    resp = await client.get(f"/api/v1/departments/{dept_id}/teams/{team_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == team_id


@pytest.mark.asyncio
async def test_update_team(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    dept_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"UpdTeam Dept {uuid.uuid4().hex[:8]}", "sort_order": 13},
        headers=headers,
    )
    dept_id = dept_resp.json()["id"]

    team_resp = await client.post(
        f"/api/v1/departments/{dept_id}/teams",
        json={"name": "Old Team Name"},
        headers=headers,
    )
    team_id = team_resp.json()["id"]

    new_name = f"New Team {uuid.uuid4().hex[:6]}"
    resp = await client.patch(
        f"/api/v1/departments/{dept_id}/teams/{team_id}",
        json={"name": new_name},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == new_name


@pytest.mark.asyncio
async def test_delete_team_empty(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    dept_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"DelTeam Dept {uuid.uuid4().hex[:8]}", "sort_order": 14},
        headers=headers,
    )
    dept_id = dept_resp.json()["id"]

    team_resp = await client.post(
        f"/api/v1/departments/{dept_id}/teams",
        json={"name": "Empty Team"},
        headers=headers,
    )
    team_id = team_resp.json()["id"]

    resp = await client.delete(
        f"/api/v1/departments/{dept_id}/teams/{team_id}",
        headers=headers,
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_create_team_duplicate_name(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    dept_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"DupeTeam Dept {uuid.uuid4().hex[:8]}", "sort_order": 15},
        headers=headers,
    )
    dept_id = dept_resp.json()["id"]

    await client.post(
        f"/api/v1/departments/{dept_id}/teams",
        json={"name": "Same Name"},
        headers=headers,
    )
    resp = await client.post(
        f"/api/v1/departments/{dept_id}/teams",
        json={"name": "Same Name"},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_delete_dept_with_teams(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    dept_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"HasTeams Dept {uuid.uuid4().hex[:8]}", "sort_order": 16},
        headers=headers,
    )
    dept_id = dept_resp.json()["id"]

    await client.post(
        f"/api/v1/departments/{dept_id}/teams",
        json={"name": "Blocking Team"},
        headers=headers,
    )

    resp = await client.delete(f"/api/v1/departments/{dept_id}", headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_department_name_conflict(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    name_a = f"Conflict A {uuid.uuid4().hex[:6]}"
    name_b = f"Conflict B {uuid.uuid4().hex[:6]}"

    resp_a = await client.post(
        "/api/v1/departments",
        json={"name": name_a, "sort_order": 17},
        headers=headers,
    )
    resp_b = await client.post(
        "/api/v1/departments",
        json={"name": name_b, "sort_order": 18},
        headers=headers,
    )
    dept_b_id = resp_b.json()["id"]

    resp = await client.patch(
        f"/api/v1/departments/{dept_b_id}",
        json={"name": name_a},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_team_not_found(client: AsyncClient, admin_user: User):
    headers = await _get_auth_headers(client, admin_user.email, "AdminPass1")
    dept_resp = await client.post(
        "/api/v1/departments",
        json={"name": f"NotFound Dept {uuid.uuid4().hex[:8]}", "sort_order": 19},
        headers=headers,
    )
    dept_id = dept_resp.json()["id"]
    resp = await client.get(
        f"/api/v1/departments/{dept_id}/teams/{uuid.uuid4()}",
        headers=headers,
    )
    assert resp.status_code == 404
