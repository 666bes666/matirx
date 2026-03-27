import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "backend"))

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.assessment import AggregatedScore, AssessmentCampaign
from app.models.career_path import CareerPath, CareerPathRequirement
from app.models.competency import Competency, CompetencyCategory
from app.models.department import Department
from app.models.enums import CampaignScope, CampaignStatus, CompetencyCategoryType, UserRole
from app.models.user import User
from tests.backend.conftest import get_auth_headers


@pytest_asyncio.fixture
async def dept_a(db: AsyncSession) -> Department:
    d = Department(name=f"CP Dept A {uuid.uuid4().hex[:8]}", sort_order=50)
    db.add(d)
    await db.flush()
    return d


@pytest_asyncio.fixture
async def dept_b(db: AsyncSession) -> Department:
    d = Department(name=f"CP Dept B {uuid.uuid4().hex[:8]}", sort_order=51)
    db.add(d)
    await db.flush()
    return d


@pytest_asyncio.fixture
async def cp_category(db: AsyncSession) -> CompetencyCategory:
    cat = CompetencyCategory(
        name=CompetencyCategoryType.HARD_SKILL,
        description="CP hard skills",
    )
    db.add(cat)
    await db.flush()
    return cat


@pytest_asyncio.fixture
async def cp_competency(db: AsyncSession, cp_category: CompetencyCategory) -> Competency:
    comp = Competency(
        category_id=cp_category.id,
        name=f"CP Competency {uuid.uuid4().hex[:8]}",
    )
    db.add(comp)
    await db.flush()
    return comp


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    u = User(
        email=f"cp_admin_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("AdminPass1"),
        first_name="Admin",
        last_name="CP",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def employee_user(db: AsyncSession, dept_a: Department) -> User:
    u = User(
        email=f"cp_emp_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("EmpPass1a"),
        first_name="Emp",
        last_name="CP",
        role=UserRole.EMPLOYEE,
        department_id=dept_a.id,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def another_employee(db: AsyncSession, dept_b: Department) -> User:
    u = User(
        email=f"cp_emp2_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("EmpPass2b"),
        first_name="Emp2",
        last_name="CP",
        role=UserRole.EMPLOYEE,
        department_id=dept_b.id,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def career_path(
    db: AsyncSession, dept_a: Department, dept_b: Department
) -> CareerPath:
    cp = CareerPath(
        from_department_id=dept_a.id,
        to_department_id=dept_b.id,
    )
    db.add(cp)
    await db.flush()
    return cp


@pytest_asyncio.fixture
async def campaign(db: AsyncSession) -> AssessmentCampaign:
    today = date.today()
    c = AssessmentCampaign(
        name=f"CP Campaign {uuid.uuid4().hex[:8]}",
        scope=CampaignScope.DIVISION,
        start_date=today - timedelta(days=30),
        end_date=today - timedelta(days=1),
        status=CampaignStatus.FINALIZED,
    )
    db.add(c)
    await db.flush()
    return c


@pytest_asyncio.fixture
async def agg_score(
    db: AsyncSession,
    campaign: AssessmentCampaign,
    employee_user: User,
    cp_competency: Competency,
) -> AggregatedScore:
    score = AggregatedScore(
        campaign_id=campaign.id,
        user_id=employee_user.id,
        competency_id=cp_competency.id,
        final_score=3.0,
    )
    db.add(score)
    await db.flush()
    return score


class TestListPaths:
    async def test_list_empty(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get("/api/v1/career-paths", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_with_data(
        self,
        client: AsyncClient,
        admin_user: User,
        career_path: CareerPath,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get("/api/v1/career-paths", headers=headers)
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert str(career_path.id) in ids


class TestCreatePath:
    async def test_create_success(
        self,
        client: AsyncClient,
        admin_user: User,
        dept_a: Department,
        dept_b: Department,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.post(
            "/api/v1/career-paths",
            json={
                "from_department_id": str(dept_a.id),
                "to_department_id": str(dept_b.id),
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["from_department_id"] == str(dept_a.id)
        assert data["to_department_id"] == str(dept_b.id)
        assert data["is_active"] is True

    async def test_create_duplicate(
        self,
        client: AsyncClient,
        admin_user: User,
        career_path: CareerPath,
        dept_a: Department,
        dept_b: Department,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.post(
            "/api/v1/career-paths",
            json={
                "from_department_id": str(dept_a.id),
                "to_department_id": str(dept_b.id),
            },
            headers=headers,
        )
        assert resp.status_code == 409


class TestGetPath:
    async def test_get_exists(
        self,
        client: AsyncClient,
        admin_user: User,
        career_path: CareerPath,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get(f"/api/v1/career-paths/{career_path.id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == str(career_path.id)

    async def test_get_not_found(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get(f"/api/v1/career-paths/{uuid.uuid4()}", headers=headers)
        assert resp.status_code == 404


class TestDeletePath:
    async def test_delete_success(
        self,
        client: AsyncClient,
        admin_user: User,
        dept_a: Department,
        dept_b: Department,
        db: AsyncSession,
    ):
        cp = CareerPath(
            from_department_id=dept_a.id,
            to_department_id=dept_b.id,
        )
        db.add(cp)
        await db.flush()

        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.delete(f"/api/v1/career-paths/{cp.id}", headers=headers)
        assert resp.status_code == 204


class TestSetRequirements:
    async def test_set_requirements(
        self,
        client: AsyncClient,
        admin_user: User,
        career_path: CareerPath,
        cp_competency: Competency,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.put(
            f"/api/v1/career-paths/{career_path.id}/requirements",
            json=[
                {
                    "competency_id": str(cp_competency.id),
                    "required_level": 3,
                    "is_mandatory": True,
                }
            ],
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["requirements"]) == 1
        req = data["requirements"][0]
        assert req["competency_id"] == str(cp_competency.id)
        assert req["required_level"] == 3
        assert req["is_mandatory"] is True


class TestGetReadiness:
    async def test_readiness_is_ready(
        self,
        client: AsyncClient,
        admin_user: User,
        career_path: CareerPath,
        cp_competency: Competency,
        employee_user: User,
        agg_score: AggregatedScore,
        db: AsyncSession,
    ):
        req = CareerPathRequirement(
            career_path_id=career_path.id,
            competency_id=cp_competency.id,
            required_level=2,
            is_mandatory=True,
        )
        db.add(req)
        await db.flush()

        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get(
            f"/api/v1/career-paths/{career_path.id}/readiness/{employee_user.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_ready"] is True
        assert data["mandatory_met"] is True
        assert data["readiness_pct"] == 100.0

    async def test_readiness_not_ready(
        self,
        client: AsyncClient,
        admin_user: User,
        career_path: CareerPath,
        cp_competency: Competency,
        employee_user: User,
        agg_score: AggregatedScore,
        db: AsyncSession,
    ):
        req = CareerPathRequirement(
            career_path_id=career_path.id,
            competency_id=cp_competency.id,
            required_level=4,
            is_mandatory=True,
        )
        db.add(req)
        await db.flush()

        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get(
            f"/api/v1/career-paths/{career_path.id}/readiness/{employee_user.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_ready"] is False
        assert data["mandatory_met"] is False

    async def test_readiness_empty_requirements(
        self,
        client: AsyncClient,
        admin_user: User,
        career_path: CareerPath,
        employee_user: User,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get(
            f"/api/v1/career-paths/{career_path.id}/readiness/{employee_user.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["readiness_pct"] == 0.0
        assert data["mandatory_met"] is True

    async def test_readiness_employee_cannot_view_other(
        self,
        client: AsyncClient,
        employee_user: User,
        another_employee: User,
        career_path: CareerPath,
    ):
        headers = await get_auth_headers(client, employee_user.email, "EmpPass1a")
        resp = await client.get(
            f"/api/v1/career-paths/{career_path.id}/readiness/{another_employee.id}",
            headers=headers,
        )
        assert resp.status_code == 403
