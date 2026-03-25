import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.department import Department
from app.models.enums import UserRole
from app.models.team import Team
from app.models.user import User
from tests.backend.conftest import get_auth_headers


@pytest_asyncio.fixture
async def team(db: AsyncSession, department: Department) -> Team:
    t = Team(name=f"Team {uuid.uuid4().hex[:8]}", department_id=department.id)
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def hr_user(db: AsyncSession) -> User:
    user = User(
        email=f"hr_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("HrPass123"),
        first_name="HR",
        last_name="Manager",
        role=UserRole.HR,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def dept_head_user(db: AsyncSession, department: Department) -> User:
    user = User(
        email=f"depthead_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("DeptPass1"),
        first_name="Dept",
        last_name="Head",
        role=UserRole.DEPARTMENT_HEAD,
        department_id=department.id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def team_lead_user(db: AsyncSession, department: Department, team: Team) -> User:
    user = User(
        email=f"tl_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TlPass1234"),
        first_name="Team",
        last_name="Lead",
        role=UserRole.TEAM_LEAD,
        department_id=department.id,
        team_id=team.id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def _admin_headers(client: AsyncClient, admin_user: User) -> dict:
    return await get_auth_headers(client, admin_user.email, "AdminPass1")


async def _hr_headers(client: AsyncClient, hr_user: User) -> dict:
    return await get_auth_headers(client, hr_user.email, "HrPass123")


async def _employee_headers(client: AsyncClient, active_user: User) -> dict:
    return await get_auth_headers(client, active_user.email, "TestPass1")


class TestListUsers:
    async def test_admin_sees_all(self, client: AsyncClient, admin_user: User, active_user: User):
        headers = await _admin_headers(client, admin_user)
        resp = await client.get("/api/v1/users", headers=headers)
        assert resp.status_code == 200
        ids = [u["id"] for u in resp.json()]
        assert str(admin_user.id) in ids
        assert str(active_user.id) in ids

    async def test_employee_sees_only_self(
        self, client: AsyncClient, active_user: User, admin_user: User
    ):
        headers = await _employee_headers(client, active_user)
        resp = await client.get("/api/v1/users", headers=headers)
        assert resp.status_code == 200
        users = resp.json()
        assert len(users) == 1
        assert users[0]["id"] == str(active_user.id)

    async def test_search_by_name(self, client: AsyncClient, admin_user: User, active_user: User):
        headers = await _admin_headers(client, admin_user)
        resp = await client.get(
            "/api/v1/users", headers=headers, params={"search": active_user.first_name}
        )
        assert resp.status_code == 200
        ids = [u["id"] for u in resp.json()]
        assert str(active_user.id) in ids

    async def test_filter_by_is_active(self, client: AsyncClient, admin_user: User, inactive_user: User):
        headers = await _admin_headers(client, admin_user)
        resp = await client.get("/api/v1/users", headers=headers, params={"is_active": "false"})
        assert resp.status_code == 200
        ids = [u["id"] for u in resp.json()]
        assert str(inactive_user.id) in ids

    async def test_filter_by_department(
        self, client: AsyncClient, admin_user: User, active_user: User
    ):
        headers = await _admin_headers(client, admin_user)
        resp = await client.get(
            "/api/v1/users",
            headers=headers,
            params={"department_id": str(active_user.department_id)},
        )
        assert resp.status_code == 200
        ids = [u["id"] for u in resp.json()]
        assert str(active_user.id) in ids

    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 401


class TestGetUser:
    async def test_admin_can_get_any_user(
        self, client: AsyncClient, admin_user: User, active_user: User
    ):
        headers = await _admin_headers(client, admin_user)
        resp = await client.get(f"/api/v1/users/{active_user.id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(active_user.id)
        assert "department" in data
        assert "team" in data

    async def test_employee_cannot_get_other_user(
        self, client: AsyncClient, active_user: User, admin_user: User
    ):
        headers = await _employee_headers(client, active_user)
        resp = await client.get(f"/api/v1/users/{admin_user.id}", headers=headers)
        assert resp.status_code == 403

    async def test_employee_can_get_self(self, client: AsyncClient, active_user: User):
        headers = await _employee_headers(client, active_user)
        resp = await client.get(f"/api/v1/users/{active_user.id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == str(active_user.id)

    async def test_get_me_endpoint(self, client: AsyncClient, active_user: User):
        headers = await _employee_headers(client, active_user)
        resp = await client.get("/api/v1/users/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == str(active_user.id)

    async def test_not_found(self, client: AsyncClient, admin_user: User):
        headers = await _admin_headers(client, admin_user)
        resp = await client.get(f"/api/v1/users/{uuid.uuid4()}", headers=headers)
        assert resp.status_code == 404


class TestCreateUser:
    async def test_admin_can_create(self, client: AsyncClient, admin_user: User):
        headers = await _admin_headers(client, admin_user)
        payload = {
            "email": f"new_{uuid.uuid4().hex[:8]}@example.com",
            "password": "NewPass123",
            "first_name": "New",
            "last_name": "User",
        }
        resp = await client.post("/api/v1/users", json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == payload["email"]
        assert data["is_active"] is False

    async def test_hr_can_create(self, client: AsyncClient, hr_user: User):
        headers = await _hr_headers(client, hr_user)
        payload = {
            "email": f"new_{uuid.uuid4().hex[:8]}@example.com",
            "password": "NewPass123",
            "first_name": "New",
            "last_name": "User",
        }
        resp = await client.post("/api/v1/users", json=payload, headers=headers)
        assert resp.status_code == 201

    async def test_employee_cannot_create(self, client: AsyncClient, active_user: User):
        headers = await _employee_headers(client, active_user)
        payload = {
            "email": f"new_{uuid.uuid4().hex[:8]}@example.com",
            "password": "NewPass123",
            "first_name": "New",
            "last_name": "User",
        }
        resp = await client.post("/api/v1/users", json=payload, headers=headers)
        assert resp.status_code == 403

    async def test_duplicate_email_returns_409(self, client: AsyncClient, admin_user: User, active_user: User):
        headers = await _admin_headers(client, admin_user)
        payload = {
            "email": active_user.email,
            "password": "NewPass123",
            "first_name": "Dup",
            "last_name": "User",
        }
        resp = await client.post("/api/v1/users", json=payload, headers=headers)
        assert resp.status_code == 409

    async def test_weak_password_returns_422(self, client: AsyncClient, admin_user: User):
        headers = await _admin_headers(client, admin_user)
        payload = {
            "email": f"new_{uuid.uuid4().hex[:8]}@example.com",
            "password": "weak",
            "first_name": "New",
            "last_name": "User",
        }
        resp = await client.post("/api/v1/users", json=payload, headers=headers)
        assert resp.status_code == 422


class TestUpdateUser:
    async def test_admin_can_update_any_user(
        self, client: AsyncClient, admin_user: User, active_user: User
    ):
        headers = await _admin_headers(client, admin_user)
        resp = await client.patch(
            f"/api/v1/users/{active_user.id}",
            json={"position": "Senior Dev"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["position"] == "Senior Dev"

    async def test_employee_can_update_own_profile(
        self, client: AsyncClient, active_user: User
    ):
        headers = await _employee_headers(client, active_user)
        resp = await client.patch(
            f"/api/v1/users/{active_user.id}",
            json={"first_name": "Updated"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Updated"

    async def test_employee_cannot_update_other_user(
        self, client: AsyncClient, active_user: User, admin_user: User
    ):
        headers = await _employee_headers(client, active_user)
        resp = await client.patch(
            f"/api/v1/users/{admin_user.id}",
            json={"first_name": "Hacked"},
            headers=headers,
        )
        assert resp.status_code == 403


class TestActivateDeactivate:
    async def test_admin_can_activate(
        self, client: AsyncClient, admin_user: User, inactive_user: User
    ):
        headers = await _admin_headers(client, admin_user)
        resp = await client.post(
            f"/api/v1/users/{inactive_user.id}/activate", headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    async def test_admin_can_deactivate(
        self, client: AsyncClient, admin_user: User, active_user: User
    ):
        headers = await _admin_headers(client, admin_user)
        resp = await client.post(
            f"/api/v1/users/{active_user.id}/deactivate", headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_employee_cannot_activate(
        self, client: AsyncClient, active_user: User, inactive_user: User
    ):
        headers = await _employee_headers(client, active_user)
        resp = await client.post(
            f"/api/v1/users/{inactive_user.id}/activate", headers=headers
        )
        assert resp.status_code == 403

    async def test_hr_can_activate(
        self, client: AsyncClient, hr_user: User, inactive_user: User
    ):
        headers = await _hr_headers(client, hr_user)
        resp = await client.post(
            f"/api/v1/users/{inactive_user.id}/activate", headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True
