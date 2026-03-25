import pytest
import redis.asyncio as aioredis
from httpx import AsyncClient

from app.models.user import User
from tests.backend.conftest import get_auth_headers


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, active_user: User):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "TestPass1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == active_user.email
    assert "refresh_token" in resp.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, active_user: User):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "WrongPass1"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_account(client: AsyncClient, inactive_user: User):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": inactive_user.email, "password": "TestPass1"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "TestPass1"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_lockout(client: AsyncClient, active_user: User, redis_client: aioredis.Redis):
    await redis_client.delete(f"login_attempts:{active_user.email}")

    for _ in range(5):
        await client.post(
            "/api/v1/auth/login",
            json={"email": active_user.email, "password": "WrongPass1"},
        )

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "TestPass1"},
    )
    assert resp.status_code == 429

    await redis_client.delete(f"login_attempts:{active_user.email}")


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "NewPass12",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "user_id" in data


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short",
            "first_name": "Weak",
            "last_name": "Pass",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, active_user: User):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": active_user.email,
            "password": "DupePass1",
            "first_name": "Dupe",
            "last_name": "User",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, active_user: User):
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "TestPass1"},
    )
    assert login_resp.status_code == 200

    refresh_resp = await client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_refresh_without_cookie(client: AsyncClient):
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, active_user: User):
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "TestPass1"},
    )
    token = login_resp.json()["access_token"]

    logout_resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_resp.status_code == 204

    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, active_user: User):
    headers = await get_auth_headers(client, active_user.email, "TestPass1")
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == active_user.email


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
