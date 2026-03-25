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
from app.models.assessment import Assessment, AssessmentCampaign
from app.models.competency import Competency, CompetencyCategory
from app.models.department import Department
from app.models.enums import AssessorType, AssessmentStatus, CampaignScope, CampaignStatus, CompetencyCategoryType, UserRole
from app.models.user import User
from tests.backend.conftest import get_auth_headers


@pytest_asyncio.fixture
async def dept(db):
    d = Department(name=f"CL Dept {uuid.uuid4().hex[:6]}", sort_order=90)
    db.add(d)
    await db.flush()
    return d


@pytest_asyncio.fixture
async def head_user(db):
    u = User(
        email=f"head_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPass1"),
        first_name="Head",
        last_name="User",
        role=UserRole.HEAD,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def employee_user(db, dept):
    u = User(
        email=f"emp_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPass1"),
        first_name="Emp",
        last_name="User",
        role=UserRole.EMPLOYEE,
        department_id=dept.id,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def category(db):
    cat = CompetencyCategory(name=CompetencyCategoryType.HARD_SKILL, description="CL test")
    db.add(cat)
    await db.flush()
    return cat


@pytest_asyncio.fixture
async def competency(db, category):
    comp = Competency(category_id=category.id, name=f"CL Comp {uuid.uuid4().hex[:6]}")
    db.add(comp)
    await db.flush()
    return comp


@pytest_asyncio.fixture
async def campaign(db, head_user):
    today = date.today()
    c = AssessmentCampaign(
        name=f"CL Campaign {uuid.uuid4().hex[:6]}",
        scope=CampaignScope.DIVISION,
        start_date=today,
        end_date=today + timedelta(days=30),
        status=CampaignStatus.DRAFT,
        created_by=head_user.id,
    )
    db.add(c)
    await db.flush()
    return c


@pytest_asyncio.fixture
async def completed_assessment(db, campaign, employee_user, head_user, competency):
    assessment = Assessment(
        campaign_id=campaign.id,
        assessee_id=employee_user.id,
        assessor_id=head_user.id,
        assessor_type=AssessorType.SELF,
        status=AssessmentStatus.COMPLETED,
    )
    db.add(assessment)
    await db.flush()
    from app.models.assessment import AssessmentScore
    score = AssessmentScore(
        assessment_id=assessment.id,
        competency_id=competency.id,
        score=3,
        is_draft=False,
    )
    db.add(score)
    await db.flush()
    return assessment


class TestCampaignLifecycle:
    async def test_activate_campaign(self, client, campaign, head_user):
        headers = await get_auth_headers(client, head_user.email, "TestPass1")
        resp = await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/activate", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    async def test_activate_invalid_state(self, client, campaign, head_user):
        headers = await get_auth_headers(client, head_user.email, "TestPass1")
        await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/activate", headers=headers)
        resp = await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/activate", headers=headers)
        assert resp.status_code == 409

    async def test_close_then_finalize(self, client, campaign, head_user, completed_assessment):
        headers = await get_auth_headers(client, head_user.email, "TestPass1")
        await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/activate", headers=headers)
        resp = await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/close", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "calibration"
        resp = await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/finalize", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "finalized"

    async def test_archive_after_finalize(self, client, campaign, head_user, completed_assessment):
        headers = await get_auth_headers(client, head_user.email, "TestPass1")
        await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/activate", headers=headers)
        await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/finalize", headers=headers)
        resp = await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/archive", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"

    async def test_progress_endpoint(self, client, campaign, head_user, completed_assessment):
        headers = await get_auth_headers(client, head_user.email, "TestPass1")
        resp = await client.get(f"/api/v1/assessments/campaigns/{campaign.id}/progress", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_assessments"] == 1
        assert data["completed_assessments"] == 1
        assert data["completion_pct"] == 100.0

    async def test_aggregated_scores_after_finalize(
        self, client, campaign, head_user, completed_assessment
    ):
        headers = await get_auth_headers(client, head_user.email, "TestPass1")
        await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/activate", headers=headers)
        await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/finalize", headers=headers)
        resp = await client.get(f"/api/v1/assessments/campaigns/{campaign.id}/scores", headers=headers)
        assert resp.status_code == 200
        scores = resp.json()
        assert len(scores) >= 1
        assert scores[0]["final_score"] == pytest.approx(3.0, abs=0.1)

    async def test_set_weights(self, client, campaign, admin_user):
        headers = await get_auth_headers(client, admin_user.email, "AdminPass1")
        resp = await client.put(
            f"/api/v1/assessments/campaigns/{campaign.id}/weights",
            json={
                "department_head_weight": 0.40,
                "team_lead_weight": 0.30,
                "self_weight": 0.20,
                "peer_weight": 0.10,
            },
            headers=headers,
        )
        assert resp.status_code == 200

    async def test_employee_cannot_activate(self, client, campaign, employee_user):
        headers = await get_auth_headers(client, employee_user.email, "TestPass1")
        resp = await client.post(f"/api/v1/assessments/campaigns/{campaign.id}/activate", headers=headers)
        assert resp.status_code == 403
