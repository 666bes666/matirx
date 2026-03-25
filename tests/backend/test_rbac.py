import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "backend"))

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.competency import CompetencyCategory
from app.models.department import Department
from app.models.enums import CompetencyCategoryType, UserRole
from app.models.team import Team
from app.models.user import User
from tests.backend.conftest import get_auth_headers


@pytest_asyncio.fixture
async def dept_a(db: AsyncSession) -> Department:
    d = Department(name=f"RBAC Dept A {uuid.uuid4().hex[:6]}", sort_order=80)
    db.add(d)
    await db.flush()
    return d


@pytest_asyncio.fixture
async def dept_b(db: AsyncSession) -> Department:
    d = Department(name=f"RBAC Dept B {uuid.uuid4().hex[:6]}", sort_order=81)
    db.add(d)
    await db.flush()
    return d


@pytest_asyncio.fixture
async def team_a(db: AsyncSession, dept_a: Department) -> Team:
    t = Team(name=f"RBAC Team A {uuid.uuid4().hex[:6]}", department_id=dept_a.id)
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def category(db: AsyncSession) -> CompetencyCategory:
    cat = CompetencyCategory(name=CompetencyCategoryType.SOFT_SKILL, description="RBAC test")
    db.add(cat)
    await db.flush()
    return cat


def _make_user(role: UserRole, dept: Department | None = None, team: Team | None = None) -> dict:
    return {
        "email": f"{role.value}_{uuid.uuid4().hex[:8]}@rbac.example.com",
        "password_hash": hash_password("TestPass1"),
        "first_name": role.value.capitalize(),
        "last_name": "RBAC",
        "role": role,
        "department_id": dept.id if dept else None,
        "team_id": team.id if team else None,
        "is_active": True,
    }


@pytest_asyncio.fixture
async def rbac_admin(db: AsyncSession) -> User:
    u = User(**_make_user(UserRole.ADMIN))
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def rbac_head(db: AsyncSession) -> User:
    u = User(**_make_user(UserRole.HEAD))
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def rbac_dept_head_a(db: AsyncSession, dept_a: Department) -> User:
    u = User(**_make_user(UserRole.DEPARTMENT_HEAD, dept=dept_a))
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def rbac_team_lead_a(db: AsyncSession, dept_a: Department, team_a: Team) -> User:
    u = User(**_make_user(UserRole.TEAM_LEAD, dept=dept_a, team=team_a))
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def rbac_hr(db: AsyncSession) -> User:
    u = User(**_make_user(UserRole.HR))
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def rbac_employee(db: AsyncSession, dept_a: Department) -> User:
    u = User(**_make_user(UserRole.EMPLOYEE, dept=dept_a))
    db.add(u)
    await db.flush()
    return u


class TestDepartmentRBAC:
    async def test_admin_can_create_dept(self, client: AsyncClient, rbac_admin: User):
        headers = await get_auth_headers(client, rbac_admin.email, "TestPass1")
        resp = await client.post(
            "/api/v1/departments",
            json={"name": f"New Dept {uuid.uuid4().hex[:6]}", "sort_order": 99},
            headers=headers,
        )
        assert resp.status_code == 201

    async def test_head_can_create_dept(self, client: AsyncClient, rbac_head: User):
        headers = await get_auth_headers(client, rbac_head.email, "TestPass1")
        resp = await client.post(
            "/api/v1/departments",
            json={"name": f"Head Dept {uuid.uuid4().hex[:6]}", "sort_order": 99},
            headers=headers,
        )
        assert resp.status_code == 201

    async def test_dept_head_cannot_create_dept(
        self, client: AsyncClient, rbac_dept_head_a: User
    ):
        headers = await get_auth_headers(client, rbac_dept_head_a.email, "TestPass1")
        resp = await client.post(
            "/api/v1/departments",
            json={"name": f"DH Dept {uuid.uuid4().hex[:6]}", "sort_order": 99},
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_employee_cannot_create_dept(self, client: AsyncClient, rbac_employee: User):
        headers = await get_auth_headers(client, rbac_employee.email, "TestPass1")
        resp = await client.post(
            "/api/v1/departments",
            json={"name": f"Emp Dept {uuid.uuid4().hex[:6]}", "sort_order": 99},
            headers=headers,
        )
        assert resp.status_code == 403


class TestTeamRBAC:
    async def test_dept_head_can_create_team_in_own_dept(
        self, client: AsyncClient, rbac_dept_head_a: User, dept_a: Department
    ):
        headers = await get_auth_headers(client, rbac_dept_head_a.email, "TestPass1")
        resp = await client.post(
            f"/api/v1/departments/{dept_a.id}/teams",
            json={"name": f"DH Team {uuid.uuid4().hex[:6]}"},
            headers=headers,
        )
        assert resp.status_code == 201

    async def test_dept_head_cannot_create_team_in_other_dept(
        self, client: AsyncClient, rbac_dept_head_a: User, dept_b: Department
    ):
        headers = await get_auth_headers(client, rbac_dept_head_a.email, "TestPass1")
        resp = await client.post(
            f"/api/v1/departments/{dept_b.id}/teams",
            json={"name": f"Wrong Dept Team {uuid.uuid4().hex[:6]}"},
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_team_lead_cannot_create_team(
        self, client: AsyncClient, rbac_team_lead_a: User, dept_a: Department
    ):
        headers = await get_auth_headers(client, rbac_team_lead_a.email, "TestPass1")
        resp = await client.post(
            f"/api/v1/departments/{dept_a.id}/teams",
            json={"name": f"TL Team {uuid.uuid4().hex[:6]}"},
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_employee_cannot_create_team(
        self, client: AsyncClient, rbac_employee: User, dept_a: Department
    ):
        headers = await get_auth_headers(client, rbac_employee.email, "TestPass1")
        resp = await client.post(
            f"/api/v1/departments/{dept_a.id}/teams",
            json={"name": f"Emp Team {uuid.uuid4().hex[:6]}"},
            headers=headers,
        )
        assert resp.status_code == 403


class TestTargetProfileRBAC:
    async def test_dept_head_can_create_in_own_dept(
        self, client: AsyncClient, rbac_dept_head_a: User, dept_a: Department
    ):
        headers = await get_auth_headers(client, rbac_dept_head_a.email, "TestPass1")
        resp = await client.post(
            "/api/v1/target-profiles",
            json={
                "name": f"Profile {uuid.uuid4().hex[:6]}",
                "department_id": str(dept_a.id),
            },
            headers=headers,
        )
        assert resp.status_code == 201

    async def test_dept_head_cannot_create_in_other_dept(
        self, client: AsyncClient, rbac_dept_head_a: User, dept_b: Department
    ):
        headers = await get_auth_headers(client, rbac_dept_head_a.email, "TestPass1")
        resp = await client.post(
            "/api/v1/target-profiles",
            json={
                "name": f"Profile {uuid.uuid4().hex[:6]}",
                "department_id": str(dept_b.id),
            },
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_team_lead_cannot_create_profile(
        self, client: AsyncClient, rbac_team_lead_a: User, dept_a: Department
    ):
        headers = await get_auth_headers(client, rbac_team_lead_a.email, "TestPass1")
        resp = await client.post(
            "/api/v1/target-profiles",
            json={
                "name": f"TL Profile {uuid.uuid4().hex[:6]}",
                "department_id": str(dept_a.id),
            },
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_employee_cannot_create_profile(
        self, client: AsyncClient, rbac_employee: User, dept_a: Department
    ):
        headers = await get_auth_headers(client, rbac_employee.email, "TestPass1")
        resp = await client.post(
            "/api/v1/target-profiles",
            json={
                "name": f"Emp Profile {uuid.uuid4().hex[:6]}",
                "department_id": str(dept_a.id),
            },
            headers=headers,
        )
        assert resp.status_code == 403


class TestCompetencyRBAC:
    async def test_admin_can_create(
        self, client: AsyncClient, rbac_admin: User, category: CompetencyCategory
    ):
        headers = await get_auth_headers(client, rbac_admin.email, "TestPass1")
        resp = await client.post(
            "/api/v1/competencies",
            json={"name": f"Comp {uuid.uuid4().hex[:6]}", "category_id": str(category.id)},
            headers=headers,
        )
        assert resp.status_code == 201

    async def test_dept_head_can_create(
        self, client: AsyncClient, rbac_dept_head_a: User, category: CompetencyCategory
    ):
        headers = await get_auth_headers(client, rbac_dept_head_a.email, "TestPass1")
        resp = await client.post(
            "/api/v1/competencies",
            json={"name": f"DH Comp {uuid.uuid4().hex[:6]}", "category_id": str(category.id)},
            headers=headers,
        )
        assert resp.status_code == 201

    async def test_team_lead_cannot_create(
        self, client: AsyncClient, rbac_team_lead_a: User, category: CompetencyCategory
    ):
        headers = await get_auth_headers(client, rbac_team_lead_a.email, "TestPass1")
        resp = await client.post(
            "/api/v1/competencies",
            json={"name": f"TL Comp {uuid.uuid4().hex[:6]}", "category_id": str(category.id)},
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_employee_cannot_create(
        self, client: AsyncClient, rbac_employee: User, category: CompetencyCategory
    ):
        headers = await get_auth_headers(client, rbac_employee.email, "TestPass1")
        resp = await client.post(
            "/api/v1/competencies",
            json={"name": f"Emp Comp {uuid.uuid4().hex[:6]}", "category_id": str(category.id)},
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_hr_cannot_create(
        self, client: AsyncClient, rbac_hr: User, category: CompetencyCategory
    ):
        headers = await get_auth_headers(client, rbac_hr.email, "TestPass1")
        resp = await client.post(
            "/api/v1/competencies",
            json={"name": f"HR Comp {uuid.uuid4().hex[:6]}", "category_id": str(category.id)},
            headers=headers,
        )
        assert resp.status_code == 403


class TestUserRBAC:
    async def test_admin_can_create_user(
        self, client: AsyncClient, rbac_admin: User, dept_a: Department
    ):
        headers = await get_auth_headers(client, rbac_admin.email, "TestPass1")
        resp = await client.post(
            "/api/v1/users",
            json={
                "email": f"new_{uuid.uuid4().hex[:8]}@test.com",
                "password": "NewPass123",
                "first_name": "New",
                "last_name": "User",
                "role": "employee",
                "department_id": str(dept_a.id),
            },
            headers=headers,
        )
        assert resp.status_code == 201

    async def test_employee_cannot_create_user(
        self, client: AsyncClient, rbac_employee: User, dept_a: Department
    ):
        headers = await get_auth_headers(client, rbac_employee.email, "TestPass1")
        resp = await client.post(
            "/api/v1/users",
            json={
                "email": f"new_{uuid.uuid4().hex[:8]}@test.com",
                "password": "NewPass123",
                "first_name": "New",
                "last_name": "User",
                "role": "employee",
                "department_id": str(dept_a.id),
            },
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_hr_can_list_users(self, client: AsyncClient, rbac_hr: User):
        headers = await get_auth_headers(client, rbac_hr.email, "TestPass1")
        resp = await client.get("/api/v1/users", headers=headers)
        assert resp.status_code == 200

    async def test_all_roles_can_read_list(
        self, client: AsyncClient, rbac_employee: User, rbac_team_lead_a: User
    ):
        for user in [rbac_employee, rbac_team_lead_a]:
            headers = await get_auth_headers(client, user.email, "TestPass1")
            resp = await client.get("/api/v1/users", headers=headers)
            assert resp.status_code == 200


class TestCampaignRBAC:
    async def test_head_can_create_campaign(self, client: AsyncClient, rbac_head: User):
        headers = await get_auth_headers(client, rbac_head.email, "TestPass1")
        today = date.today()
        resp = await client.post(
            "/api/v1/assessments/campaigns",
            json={
                "name": f"Campaign {uuid.uuid4().hex[:6]}",
                "scope": "division",
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=30)).isoformat(),
            },
            headers=headers,
        )
        assert resp.status_code == 201

    async def test_team_lead_cannot_create_campaign(
        self, client: AsyncClient, rbac_team_lead_a: User
    ):
        headers = await get_auth_headers(client, rbac_team_lead_a.email, "TestPass1")
        today = date.today()
        resp = await client.post(
            "/api/v1/assessments/campaigns",
            json={
                "name": f"Campaign {uuid.uuid4().hex[:6]}",
                "scope": "division",
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=30)).isoformat(),
            },
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_employee_cannot_create_campaign(
        self, client: AsyncClient, rbac_employee: User
    ):
        headers = await get_auth_headers(client, rbac_employee.email, "TestPass1")
        today = date.today()
        resp = await client.post(
            "/api/v1/assessments/campaigns",
            json={
                "name": f"Campaign {uuid.uuid4().hex[:6]}",
                "scope": "division",
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=30)).isoformat(),
            },
            headers=headers,
        )
        assert resp.status_code == 403


class TestAnalyticsRBAC:
    async def test_all_authenticated_roles_can_access_matrix(
        self,
        client: AsyncClient,
        rbac_admin: User,
        rbac_head: User,
        rbac_dept_head_a: User,
        rbac_team_lead_a: User,
        rbac_hr: User,
        rbac_employee: User,
    ):
        for user in [rbac_admin, rbac_head, rbac_dept_head_a, rbac_team_lead_a, rbac_hr, rbac_employee]:
            headers = await get_auth_headers(client, user.email, "TestPass1")
            resp = await client.get("/api/v1/analytics/matrix", headers=headers)
            assert resp.status_code == 200, f"Failed for role {user.role}"

    async def test_unauthenticated_cannot_access_matrix(self, client: AsyncClient):
        resp = await client.get("/api/v1/analytics/matrix")
        assert resp.status_code == 401
