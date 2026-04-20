"""Magic-link auth flow tests."""

import pytest
from httpx import AsyncClient

from app.auth.magic_link.service import create_magic_link


@pytest.mark.asyncio
async def test_request_returns_202(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/magic-link/request",
        json={"email": "user@example.com", "name": "User"},
    )
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_verify_creates_user_and_household(client: AsyncClient):
    token = await create_magic_link(email="first@example.com", name="First User")
    response = await client.post("/api/v1/auth/magic-link/verify", json={"token": token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "first@example.com"

    household = await client.get("/api/v1/household")
    assert household.status_code == 200
    hh = household.json()
    assert hh["name"]
    assert len(hh["members"]) == 1
    assert hh["members"][0]["kind"] == "adult"


@pytest.mark.asyncio
async def test_verify_token_single_use(client: AsyncClient):
    token = await create_magic_link(email="single@example.com")
    first = await client.post("/api/v1/auth/magic-link/verify", json={"token": token})
    assert first.status_code == 200

    second = await client.post("/api/v1/auth/magic-link/verify", json={"token": token})
    assert second.status_code == 401


@pytest.mark.asyncio
async def test_verify_invalid_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/magic-link/verify", json={"token": "not-a-real-token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_sign_in_is_idempotent_for_existing_user(client: AsyncClient):
    token1 = await create_magic_link(email="again@example.com", name="Again")
    r1 = await client.post("/api/v1/auth/magic-link/verify", json={"token": token1})
    assert r1.status_code == 200

    token2 = await create_magic_link(email="again@example.com")
    r2 = await client.post("/api/v1/auth/magic-link/verify", json={"token": token2})
    assert r2.status_code == 200

    me = await client.get("/api/v1/auth/me")
    assert me.json()["email"] == "again@example.com"
