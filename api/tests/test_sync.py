"""Sync endpoint tests — cursor, isolation."""

import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sync_full_pull_returns_everything(client: AsyncClient, sign_in):
    await sign_in(email="sync@example.com", name="Syncer")
    household = (await client.get("/api/v1/household")).json()
    me = household["members"][0]
    areas = (await client.get("/api/v1/areas")).json()

    project = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "P",
                "area_public_id": areas[0]["public_id"],
                "lead_member_public_id": me["public_id"],
            },
        )
    ).json()

    task = (
        await client.post(
            "/api/v1/tasks",
            json={"title": "T", "project_public_id": project["public_id"]},
        )
    ).json()

    response = await client.get("/api/v1/sync")
    assert response.status_code == 200
    data = response.json()
    assert "server_time" in data
    assert len(data["areas"]) == 5
    assert len(data["projects"]) == 1
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["public_id"] == task["public_id"]


@pytest.mark.asyncio
async def test_sync_since_returns_only_changes(client: AsyncClient, sign_in):
    await sign_in(email="cursor@example.com", name="Cursor")
    household = (await client.get("/api/v1/household")).json()
    me = household["members"][0]
    areas = (await client.get("/api/v1/areas")).json()
    project = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "P",
                "area_public_id": areas[0]["public_id"],
                "lead_member_public_id": me["public_id"],
            },
        )
    ).json()

    first = await client.get("/api/v1/sync")
    cursor = first.json()["server_time"]

    # Ensure any subsequent writes land strictly after the cursor.
    await asyncio.sleep(0.05)

    empty = await client.get("/api/v1/sync", params={"since": cursor})
    assert empty.status_code == 200
    data = empty.json()
    assert len(data["tasks"]) == 0
    # projects from the bootstrap are BEFORE the cursor, so they shouldn't appear
    assert len(data["projects"]) == 0

    task = (
        await client.post(
            "/api/v1/tasks",
            json={"title": "New", "project_public_id": project["public_id"]},
        )
    ).json()

    after = await client.get("/api/v1/sync", params={"since": cursor})
    assert any(t["public_id"] == task["public_id"] for t in after.json()["tasks"])


@pytest.mark.asyncio
async def test_sync_cross_household_isolation(client: AsyncClient, sign_in):
    await sign_in(email="hh1@example.com", name="H1 User")
    household1 = (await client.get("/api/v1/household")).json()
    areas1 = (await client.get("/api/v1/areas")).json()
    project1 = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "P1",
                "area_public_id": areas1[0]["public_id"],
                "lead_member_public_id": household1["members"][0]["public_id"],
            },
        )
    ).json()
    await client.post(
        "/api/v1/tasks",
        json={"title": "secret task", "project_public_id": project1["public_id"]},
    )

    await client.post("/api/v1/auth/logout")

    await sign_in(email="hh2@example.com", name="H2 User")
    sync2 = await client.get("/api/v1/sync")
    data = sync2.json()
    assert len(data["tasks"]) == 0
    assert len(data["projects"]) == 0
    titles = [t["title"] for t in data["tasks"]]
    assert "secret task" not in titles
