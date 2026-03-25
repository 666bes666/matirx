import csv
import io
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
from app.models.competency import Competency, CompetencyCategory
from app.models.department import Department
from app.models.development_plan import DevelopmentPlan
from app.models.enums import (
    CampaignScope,
    CampaignStatus,
    CompetencyCategoryType,
    GoalStatus,
    UserRole,
)
from app.models.user import User
from tests.backend.conftest import get_auth_headers


@pytest_asyncio.fixture
async def dept(db: AsyncSession) -> Department:
    d = Department(name=f"Phase3 Dept {uuid.uuid4().hex[:8]}", sort_order=99)
    db.add(d)
    await db.flush()
    return d


@pytest_asyncio.fixture
async def category(db: AsyncSession) -> CompetencyCategory:
    cat = CompetencyCategory(
        name=CompetencyCategoryType.SOFT_SKILL,
        description="Soft skills for phase3",
    )
    db.add(cat)
    await db.flush()
    return cat


@pytest_asyncio.fixture
async def competency(db: AsyncSession, category: CompetencyCategory) -> Competency:
    comp = Competency(
        category_id=category.id,
        name=f"Phase3 Comp {uuid.uuid4().hex[:8]}",
    )
    db.add(comp)
    await db.flush()
    return comp


@pytest_asyncio.fixture
async def employee(db: AsyncSession, dept: Department) -> User:
    u = User(
        email=f"p3emp_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPass1"),
        first_name="Emp",
        last_name="Phase3",
        role=UserRole.EMPLOYEE,
        department_id=dept.id,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    u = User(
        email=f"p3admin_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("AdminPass1"),
        first_name="Admin",
        last_name="Phase3",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def hr_user(db: AsyncSession) -> User:
    u = User(
        email=f"p3hr_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("HrPass1a"),
        first_name="Hr",
        last_name="Phase3",
        role=UserRole.HR,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def team_lead_user(db: AsyncSession, dept: Department) -> User:
    u = User(
        email=f"p3tl_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TlPass1ab"),
        first_name="TL",
        last_name="Phase3",
        role=UserRole.TEAM_LEAD,
        department_id=dept.id,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def campaign(db: AsyncSession) -> AssessmentCampaign:
    today = date.today()
    c = AssessmentCampaign(
        name=f"P3 Campaign {uuid.uuid4().hex[:8]}",
        scope=CampaignScope.DIVISION,
        start_date=today,
        end_date=today + timedelta(days=30),
        status=CampaignStatus.FINALIZED,
    )
    db.add(c)
    await db.flush()
    return c


@pytest_asyncio.fixture
async def agg_score(
    db: AsyncSession,
    campaign: AssessmentCampaign,
    employee: User,
    competency: Competency,
) -> AggregatedScore:
    score = AggregatedScore(
        campaign_id=campaign.id,
        user_id=employee.id,
        competency_id=competency.id,
        final_score=2.5,
    )
    db.add(score)
    await db.flush()
    return score


class TestHeatmapEndpoint:
    async def test_heatmap_returns_200(
        self,
        client: AsyncClient,
        admin_user: User,
        dept: Department,
        competency: Competency,
        employee: User,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get("/api/v1/analytics/heatmap", headers=headers)
        assert resp.status_code == 200

    async def test_heatmap_structure(
        self,
        client: AsyncClient,
        admin_user: User,
        dept: Department,
        competency: Competency,
        employee: User,
        agg_score: AggregatedScore,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get("/api/v1/analytics/heatmap", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "departments" in data
        assert "competencies" in data
        assert "averages" in data
        assert isinstance(data["departments"], list)
        assert isinstance(data["competencies"], list)
        assert isinstance(data["averages"], dict)

    async def test_heatmap_department_keys(
        self,
        client: AsyncClient,
        admin_user: User,
        dept: Department,
        competency: Competency,
        employee: User,
        agg_score: AggregatedScore,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get("/api/v1/analytics/heatmap", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        dept_ids = [d["id"] for d in data["departments"]]
        assert str(dept.id) in dept_ids

    async def test_heatmap_average_value(
        self,
        client: AsyncClient,
        admin_user: User,
        dept: Department,
        competency: Competency,
        employee: User,
        agg_score: AggregatedScore,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get("/api/v1/analytics/heatmap", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        dept_str = str(dept.id)
        comp_str = str(competency.id)
        avg = data["averages"].get(dept_str, {}).get(comp_str)
        assert avg == pytest.approx(2.5)

    async def test_heatmap_filter_by_category(
        self,
        client: AsyncClient,
        admin_user: User,
        category: CompetencyCategory,
        competency: Competency,
        employee: User,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get(
            "/api/v1/analytics/heatmap",
            headers=headers,
            params={"category_id": str(category.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        comp_ids = [c["id"] for c in data["competencies"]]
        assert str(competency.id) in comp_ids

    async def test_heatmap_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/analytics/heatmap")
        assert resp.status_code == 401


class TestExportMatrix:
    async def test_export_matrix_returns_xlsx(
        self,
        client: AsyncClient,
        admin_user: User,
        employee: User,
        competency: Competency,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get("/api/v1/export/matrix.xlsx", headers=headers)
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    async def test_export_matrix_forbidden_for_employee(
        self,
        client: AsyncClient,
        employee: User,
    ):
        headers = await get_auth_headers(client, employee.email, "TestPass1")
        resp = await client.get("/api/v1/export/matrix.xlsx", headers=headers)
        assert resp.status_code == 403

    async def test_export_matrix_allowed_for_hr(
        self,
        client: AsyncClient,
        hr_user: User,
    ):
        headers = await get_auth_headers(client, hr_user.email, "HrPass1a")
        resp = await client.get("/api/v1/export/matrix.xlsx", headers=headers)
        assert resp.status_code == 200


class TestExportUserReport:
    async def test_export_user_report_xlsx(
        self,
        client: AsyncClient,
        admin_user: User,
        employee: User,
        agg_score: AggregatedScore,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get(f"/api/v1/export/users/{employee.id}/report.xlsx", headers=headers)
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    async def test_export_own_report(
        self,
        client: AsyncClient,
        employee: User,
    ):
        headers = await get_auth_headers(client, employee.email, "TestPass1")
        resp = await client.get(f"/api/v1/export/users/{employee.id}/report.xlsx", headers=headers)
        assert resp.status_code == 200

    async def test_export_other_user_report_forbidden(
        self,
        client: AsyncClient,
        employee: User,
        admin_user: User,
    ):
        headers = await get_auth_headers(client, employee.email, "TestPass1")
        resp = await client.get(f"/api/v1/export/users/{admin_user.id}/report.xlsx", headers=headers)
        assert resp.status_code == 403

    async def test_export_nonexistent_user(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get(f"/api/v1/export/users/{uuid.uuid4()}/report.xlsx", headers=headers)
        assert resp.status_code == 404


class TestIDPCRUD:
    async def test_create_plan(
        self,
        client: AsyncClient,
        team_lead_user: User,
        employee: User,
    ):
        headers = await get_auth_headers(client, team_lead_user.email, "TlPass1ab")
        resp = await client.post(
            "/api/v1/development-plans",
            json={"user_id": str(employee.id)},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"] == str(employee.id)
        assert data["status"] == "draft"

    async def test_list_plans_employee_sees_own(
        self,
        client: AsyncClient,
        employee: User,
        team_lead_user: User,
        db: AsyncSession,
    ):
        plan = DevelopmentPlan(user_id=employee.id, created_by=team_lead_user.id)
        db.add(plan)
        await db.flush()

        headers = await get_auth_headers(client, employee.email, "TestPass1")
        resp = await client.get("/api/v1/development-plans", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        plan_ids = [p["id"] for p in data]
        assert str(plan.id) in plan_ids

    async def test_get_plan(
        self,
        client: AsyncClient,
        admin_user: User,
        employee: User,
        team_lead_user: User,
        db: AsyncSession,
    ):
        plan = DevelopmentPlan(user_id=employee.id, created_by=team_lead_user.id)
        db.add(plan)
        await db.flush()

        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get(f"/api/v1/development-plans/{plan.id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(plan.id)

    async def test_add_goal(
        self,
        client: AsyncClient,
        team_lead_user: User,
        employee: User,
        competency: Competency,
        db: AsyncSession,
    ):
        plan = DevelopmentPlan(user_id=employee.id, created_by=team_lead_user.id)
        db.add(plan)
        await db.flush()

        headers = await get_auth_headers(client, team_lead_user.email, "TlPass1ab")
        resp = await client.post(
            f"/api/v1/development-plans/{plan.id}/goals",
            json={
                "competency_id": str(competency.id),
                "current_level": 1,
                "target_level": 3,
                "is_mandatory": False,
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["competency_id"] == str(competency.id)
        assert data["current_level"] == 1
        assert data["target_level"] == 3

    async def test_update_goal_status(
        self,
        client: AsyncClient,
        team_lead_user: User,
        employee: User,
        competency: Competency,
        db: AsyncSession,
    ):
        plan = DevelopmentPlan(user_id=employee.id, created_by=team_lead_user.id)
        db.add(plan)
        await db.flush()

        headers = await get_auth_headers(client, team_lead_user.email, "TlPass1ab")
        goal_resp = await client.post(
            f"/api/v1/development-plans/{plan.id}/goals",
            json={
                "competency_id": str(competency.id),
                "current_level": 0,
                "target_level": 2,
            },
            headers=headers,
        )
        assert goal_resp.status_code == 201
        goal_id = goal_resp.json()["id"]

        update_resp = await client.patch(
            f"/api/v1/development-plans/{plan.id}/goals/{goal_id}",
            json={"status": "in_progress"},
            headers=headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "in_progress"

    async def test_delete_goal(
        self,
        client: AsyncClient,
        team_lead_user: User,
        employee: User,
        competency: Competency,
        db: AsyncSession,
    ):
        plan = DevelopmentPlan(user_id=employee.id, created_by=team_lead_user.id)
        db.add(plan)
        await db.flush()

        headers = await get_auth_headers(client, team_lead_user.email, "TlPass1ab")
        goal_resp = await client.post(
            f"/api/v1/development-plans/{plan.id}/goals",
            json={
                "competency_id": str(competency.id),
                "current_level": 1,
                "target_level": 4,
            },
            headers=headers,
        )
        assert goal_resp.status_code == 201
        goal_id = goal_resp.json()["id"]

        del_resp = await client.delete(
            f"/api/v1/development-plans/{plan.id}/goals/{goal_id}",
            headers=headers,
        )
        assert del_resp.status_code == 204

    async def test_get_nonexistent_plan(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.get(f"/api/v1/development-plans/{uuid.uuid4()}", headers=headers)
        assert resp.status_code == 404

    async def test_update_plan_status(
        self,
        client: AsyncClient,
        team_lead_user: User,
        employee: User,
        db: AsyncSession,
    ):
        plan = DevelopmentPlan(user_id=employee.id, created_by=team_lead_user.id)
        db.add(plan)
        await db.flush()

        headers = await get_auth_headers(client, team_lead_user.email, "TlPass1ab")
        resp = await client.patch(
            f"/api/v1/development-plans/{plan.id}",
            json={"status": "active"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"


class TestImportUsers:
    def _make_csv(self, rows: list[dict]) -> bytes:
        fieldnames = ["email", "first_name", "last_name", "password", "role", "department", "patronymic", "position"]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            full_row = {f: row.get(f, "") for f in fieldnames}
            writer.writerow(full_row)
        return buf.getvalue().encode("utf-8")

    async def test_import_users_success(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        email = f"imported_{uuid.uuid4().hex[:8]}@example.com"
        csv_data = self._make_csv([
            {
                "email": email,
                "first_name": "Imported",
                "last_name": "User",
                "password": "ImportPass1",
                "role": "employee",
            }
        ])
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.post(
            "/api/v1/import/users",
            files={"file": ("users.csv", csv_data, "text/csv")},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 1
        assert data["errors"] == []

    async def test_import_users_duplicate_email(
        self,
        client: AsyncClient,
        admin_user: User,
        employee: User,
    ):
        csv_data = self._make_csv([
            {
                "email": employee.email,
                "first_name": "Dup",
                "last_name": "User",
                "password": "DupPass123",
                "role": "employee",
            }
        ])
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.post(
            "/api/v1/import/users",
            files={"file": ("users.csv", csv_data, "text/csv")},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 0
        assert len(data["errors"]) == 1
        assert "уже занят" in data["errors"][0]

    async def test_import_users_bad_password(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        email = f"badpwd_{uuid.uuid4().hex[:8]}@example.com"
        csv_data = self._make_csv([
            {
                "email": email,
                "first_name": "Bad",
                "last_name": "Pwd",
                "password": "weak",
                "role": "employee",
            }
        ])
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.post(
            "/api/v1/import/users",
            files={"file": ("users.csv", csv_data, "text/csv")},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 0
        assert len(data["errors"]) == 1
        assert "пароль" in data["errors"][0]

    async def test_import_users_forbidden_for_employee(
        self,
        client: AsyncClient,
        employee: User,
    ):
        import csv

        csv_data = self._make_csv([])
        headers = await get_auth_headers(client, employee.email, "TestPass1")
        resp = await client.post(
            "/api/v1/import/users",
            files={"file": ("users.csv", csv_data, "text/csv")},
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_import_users_not_csv(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.post(
            "/api/v1/import/users",
            files={"file": ("users.txt", b"hello", "text/plain")},
            headers=headers,
        )
        assert resp.status_code == 400


class TestImportCompetencies:
    def _make_csv(self, rows: list[dict]) -> bytes:
        fieldnames = ["name", "category", "description"]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            full_row = {f: row.get(f, "") for f in fieldnames}
            writer.writerow(full_row)
        return buf.getvalue().encode("utf-8")

    async def test_import_competencies_success(
        self,
        client: AsyncClient,
        admin_user: User,
        category: CompetencyCategory,
        db: AsyncSession,
    ):
        comp_name = f"Imported Comp {uuid.uuid4().hex[:8]}"
        csv_data = self._make_csv([
            {
                "name": comp_name,
                "category": category.name.value,
                "description": "Test description",
            }
        ])
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.post(
            "/api/v1/import/competencies",
            files={"file": ("comps.csv", csv_data, "text/csv")},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 1
        assert data["errors"] == []

    async def test_import_competencies_category_not_found(
        self,
        client: AsyncClient,
        admin_user: User,
    ):
        comp_name = f"NoCategory Comp {uuid.uuid4().hex[:8]}"
        csv_data = self._make_csv([
            {
                "name": comp_name,
                "category": "nonexistent_category",
            }
        ])
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.post(
            "/api/v1/import/competencies",
            files={"file": ("comps.csv", csv_data, "text/csv")},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 0
        assert len(data["errors"]) == 1
        assert "категория" in data["errors"][0].lower()

    async def test_import_competencies_duplicate(
        self,
        client: AsyncClient,
        admin_user: User,
        competency: Competency,
        category: CompetencyCategory,
    ):
        csv_data = self._make_csv([
            {
                "name": competency.name,
                "category": category.name.value,
            }
        ])
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.post(
            "/api/v1/import/competencies",
            files={"file": ("comps.csv", csv_data, "text/csv")},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 0
        assert len(data["errors"]) == 1

    async def test_import_competencies_forbidden_for_hr(
        self,
        client: AsyncClient,
        hr_user: User,
    ):
        csv_data = self._make_csv([])
        headers = await get_auth_headers(client, hr_user.email, "HrPass1a")
        resp = await client.post(
            "/api/v1/import/competencies",
            files={"file": ("comps.csv", csv_data, "text/csv")},
            headers=headers,
        )
        assert resp.status_code == 403
