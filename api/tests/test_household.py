"""Household module tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_household_has_self_member(client: AsyncClient, sign_in):
    await sign_in(email="a@example.com", name="Alpha Tester")
    response = await client.get("/api/v1/household")
    assert response.status_code == 200
    data = response.json()
    assert len(data["members"]) == 1
    assert data["members"][0]["name"] == "Alpha Tester"
    assert data["members"][0]["short"] == "AT"


@pytest.mark.asyncio
async def test_add_kid_member(client: AsyncClient, sign_in):
    await sign_in(email="mom@example.com", name="Mom")
    response = await client.post(
        "/api/v1/household/members",
        json={"name": "Gabriel", "short": "GA", "color": "#ff7eb9", "kind": "kid"},
    )
    assert response.status_code == 201
    member = response.json()
    assert member["kind"] == "kid"
    assert member["user_public_id"] is None


@pytest.mark.asyncio
async def test_update_and_delete_member(client: AsyncClient, sign_in):
    await sign_in(email="update@example.com", name="Updater")
    created = (
        await client.post(
            "/api/v1/household/members",
            json={"name": "Dad", "short": "D", "color": "#333", "kind": "external"},
        )
    ).json()

    patched = await client.patch(
        f"/api/v1/household/members/{created['public_id']}",
        json={"name": "Grandpa"},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Grandpa"

    deleted = await client.delete(f"/api/v1/household/members/{created['public_id']}")
    assert deleted.status_code == 204

    household = (await client.get("/api/v1/household")).json()
    member_ids = [m["public_id"] for m in household["members"]]
    assert created["public_id"] not in member_ids


@pytest.mark.asyncio
async def test_invite_returns_202(client: AsyncClient, sign_in):
    await sign_in(email="inviter@example.com", name="Inviter")
    response = await client.post(
        "/api/v1/household/invite",
        json={"email": "spouse@example.com"},
    )
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_cross_household_isolation(client: AsyncClient, sign_in):
    """Two independent users get separate households; each sees only their own."""
    await sign_in(email="user1@example.com", name="One")
    r1 = await client.get("/api/v1/household")
    hh1 = r1.json()

    await client.post("/api/v1/auth/logout")

    await sign_in(email="user2@example.com", name="Two")
    r2 = await client.get("/api/v1/household")
    hh2 = r2.json()

    assert hh1["public_id"] != hh2["public_id"]
    assert {m["name"] for m in hh2["members"]} == {"Two"}
