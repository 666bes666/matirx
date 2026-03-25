import uuid

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.competency import CompetencyCategory
from app.models.enums import CompetencyCategoryType, UserRole
from app.models.user import User
from tests.backend.conftest import get_auth_headers


@pytest_asyncio.fixture
async def category(db: AsyncSession) -> CompetencyCategory:
    cat = CompetencyCategory(
        name=CompetencyCategoryType.HARD_SKILL,
        description="Hard skills",
    )
    db.add(cat)
    await db.flush()
    return cat


@pytest_asyncio.fixture
async def head_user(db: AsyncSession) -> User:
    user = User(
        email=f"head_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("HeadPass12"),
        first_name="Head",
        last_name="User",
        role=UserRole.HEAD,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def _admin_headers(client: AsyncClient, admin_user: User) -> dict:
    return await get_auth_headers(client, admin_user.email, "AdminPass1")


async def _head_headers(client: AsyncClient, head_user: User) -> dict:
    return await get_auth_headers(client, head_user.email, "HeadPass12")


async def _employee_headers(client: AsyncClient, active_user: User) -> dict:
    return await get_auth_headers(client, active_user.email, "TestPass1")


class TestCategories:
    async def test_list_categories(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        resp = await client.get("/api/v1/competencies/categories", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/competencies/categories")
        assert resp.status_code == 401


class TestListCompetencies:
    async def test_list_empty(self, client: AsyncClient, admin_user: User):
        headers = await _admin_headers(client, admin_user)
        resp = await client.get("/api/v1/competencies", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_with_data(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        payload = {"category_id": str(category.id), "name": "Linux"}
        await client.post("/api/v1/competencies", json=payload, headers=headers)

        resp = await client.get("/api/v1/competencies", headers=headers)
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "Linux" in names

    async def test_filter_by_category(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        payload = {"category_id": str(category.id), "name": f"Filtered {uuid.uuid4().hex[:6]}"}
        await client.post("/api/v1/competencies", json=payload, headers=headers)

        resp = await client.get(
            "/api/v1/competencies",
            headers=headers,
            params={"category_id": str(category.id)},
        )
        assert resp.status_code == 200

    async def test_search(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        unique_name = f"UniqueComp_{uuid.uuid4().hex[:6]}"
        await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": unique_name},
            headers=headers,
        )
        resp = await client.get(
            "/api/v1/competencies", headers=headers, params={"search": unique_name}
        )
        assert resp.status_code == 200
        assert any(c["name"] == unique_name for c in resp.json())


class TestCreateCompetency:
    async def test_admin_can_create(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        name = f"Competency_{uuid.uuid4().hex[:6]}"
        resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": name, "is_common": True},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == name
        assert data["is_common"] is True
        assert data["is_archived"] is False
        assert "category" in data
        assert "level_criteria" in data

    async def test_head_can_create(
        self, client: AsyncClient, head_user: User, category: CompetencyCategory
    ):
        headers = await _head_headers(client, head_user)
        name = f"HeadComp_{uuid.uuid4().hex[:6]}"
        resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": name},
            headers=headers,
        )
        assert resp.status_code == 201

    async def test_employee_cannot_create(
        self, client: AsyncClient, active_user: User, category: CompetencyCategory
    ):
        headers = await _employee_headers(client, active_user)
        resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": "Blocked"},
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_duplicate_name_in_category_returns_409(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        name = f"DupComp_{uuid.uuid4().hex[:6]}"
        await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": name},
            headers=headers,
        )
        resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": name},
            headers=headers,
        )
        assert resp.status_code == 409

    async def test_invalid_category_returns_404(
        self, client: AsyncClient, admin_user: User
    ):
        headers = await _admin_headers(client, admin_user)
        resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(uuid.uuid4()), "name": "NoCat"},
            headers=headers,
        )
        assert resp.status_code == 404


class TestGetCompetency:
    async def test_get_existing(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        name = f"GetComp_{uuid.uuid4().hex[:6]}"
        create_resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": name},
            headers=headers,
        )
        comp_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/competencies/{comp_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == name

    async def test_not_found(self, client: AsyncClient, admin_user: User):
        headers = await _admin_headers(client, admin_user)
        resp = await client.get(f"/api/v1/competencies/{uuid.uuid4()}", headers=headers)
        assert resp.status_code == 404


class TestUpdateCompetency:
    async def test_update_name(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        create_resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": f"Old_{uuid.uuid4().hex[:6]}"},
            headers=headers,
        )
        comp_id = create_resp.json()["id"]
        new_name = f"New_{uuid.uuid4().hex[:6]}"

        resp = await client.patch(
            f"/api/v1/competencies/{comp_id}",
            json={"name": new_name},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == new_name

    async def test_employee_cannot_update(
        self, client: AsyncClient, admin_user: User, active_user: User, category: CompetencyCategory
    ):
        admin_headers = await _admin_headers(client, admin_user)
        emp_headers = await _employee_headers(client, active_user)

        create_resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": f"Comp_{uuid.uuid4().hex[:6]}"},
            headers=admin_headers,
        )
        comp_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/competencies/{comp_id}",
            json={"name": "Hacked"},
            headers=emp_headers,
        )
        assert resp.status_code == 403


class TestArchiveCompetency:
    async def test_archive_and_unarchive(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        create_resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": f"Arch_{uuid.uuid4().hex[:6]}"},
            headers=headers,
        )
        comp_id = create_resp.json()["id"]

        archive_resp = await client.post(
            f"/api/v1/competencies/{comp_id}/archive", headers=headers
        )
        assert archive_resp.status_code == 200
        assert archive_resp.json()["is_archived"] is True

        unarchive_resp = await client.post(
            f"/api/v1/competencies/{comp_id}/unarchive", headers=headers
        )
        assert unarchive_resp.status_code == 200
        assert unarchive_resp.json()["is_archived"] is False

    async def test_archived_excluded_from_default_list(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        name = f"ToArchive_{uuid.uuid4().hex[:6]}"
        create_resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": name},
            headers=headers,
        )
        comp_id = create_resp.json()["id"]
        await client.post(f"/api/v1/competencies/{comp_id}/archive", headers=headers)

        list_resp = await client.get("/api/v1/competencies", headers=headers)
        names = [c["name"] for c in list_resp.json()]
        assert name not in names


class TestCriteriaUpsert:
    async def test_upsert_criteria(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        create_resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": f"Crit_{uuid.uuid4().hex[:6]}"},
            headers=headers,
        )
        comp_id = create_resp.json()["id"]

        criteria = [
            {"level": 0, "criteria_description": "Нет знаний"},
            {"level": 1, "criteria_description": "Базовое понимание"},
            {"level": 2, "criteria_description": "Уверенное применение"},
        ]
        resp = await client.put(
            f"/api/v1/competencies/{comp_id}/criteria",
            json=criteria,
            headers=headers,
        )
        assert resp.status_code == 200
        levels = {c["level"]: c["criteria_description"] for c in resp.json()["level_criteria"]}
        assert levels[0] == "Нет знаний"
        assert levels[1] == "Базовое понимание"
        assert levels[2] == "Уверенное применение"

    async def test_update_existing_criteria(
        self, client: AsyncClient, admin_user: User, category: CompetencyCategory
    ):
        headers = await _admin_headers(client, admin_user)
        create_resp = await client.post(
            "/api/v1/competencies",
            json={"category_id": str(category.id), "name": f"Crit2_{uuid.uuid4().hex[:6]}"},
            headers=headers,
        )
        comp_id = create_resp.json()["id"]

        await client.put(
            f"/api/v1/competencies/{comp_id}/criteria",
            json=[{"level": 0, "criteria_description": "Old"}],
            headers=headers,
        )
        resp = await client.put(
            f"/api/v1/competencies/{comp_id}/criteria",
            json=[{"level": 0, "criteria_description": "Updated"}],
            headers=headers,
        )
        assert resp.status_code == 200
        levels = {c["level"]: c["criteria_description"] for c in resp.json()["level_criteria"]}
        assert levels[0] == "Updated"
