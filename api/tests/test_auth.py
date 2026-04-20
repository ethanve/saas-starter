"""Auth route tests — refresh, logout, me, health."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_after_sign_in(client: AsyncClient, sign_in):
    await sign_in(email="me@example.com", name="Me Test")
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["name"] == "Me Test"


@pytest.mark.asyncio
async def test_logout_clears_cookies(client: AsyncClient, sign_in):
    await sign_in(email="logout@example.com", name="Logout")
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
