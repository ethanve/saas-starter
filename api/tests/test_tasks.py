"""Task CRUD + step + comment tests."""

import pytest
from httpx import AsyncClient


async def _bootstrap(client: AsyncClient, sign_in) -> dict:
    await sign_in(email="owner@example.com", name="Owner")
    household = (await client.get("/api/v1/household")).json()
    me = household["members"][0]

    areas = (await client.get("/api/v1/areas")).json()
    assert len(areas) == 5

    project = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Taxes 2026",
                "area_public_id": next(a for a in areas if a["slug"] == "money")["public_id"],
                "lead_member_public_id": me["public_id"],
            },
        )
    ).json()

    return {"me": me, "areas": areas, "project": project}


@pytest.mark.asyncio
async def test_create_and_read_task(client: AsyncClient, sign_in):
    ctx = await _bootstrap(client, sign_in)
    r = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Gather W-2s",
            "project_public_id": ctx["project"]["public_id"],
            "assignee_member_public_id": ctx["me"]["public_id"],
            "status": "todo",
            "priority": "high",
            "steps": [{"id": "step_a", "title": "Find 2025 folder", "done": False}],
        },
    )
    assert r.status_code == 201, r.text
    task = r.json()
    assert task["title"] == "Gather W-2s"
    assert task["priority"] == "high"
    assert len(task["steps"]) == 1

    listing = await client.get("/api/v1/tasks")
    assert listing.status_code == 200
    assert len(listing.json()) == 1


@pytest.mark.asyncio
async def test_patch_task_updates_steps(client: AsyncClient, sign_in):
    ctx = await _bootstrap(client, sign_in)
    task = (
        await client.post(
            "/api/v1/tasks",
            json={
                "title": "School supplies",
                "project_public_id": ctx["project"]["public_id"],
                "steps": [{"id": "s1", "title": "pencils", "done": False}],
            },
        )
    ).json()

    r = await client.patch(
        f"/api/v1/tasks/{task['public_id']}",
        json={
            "steps": [
                {"id": "s1", "title": "pencils", "done": True},
                {"id": "s2", "title": "notebook", "done": False},
            ]
        },
    )
    assert r.status_code == 200
    steps = r.json()["steps"]
    assert len(steps) == 2
    assert steps[0]["done"] is True


@pytest.mark.asyncio
async def test_soft_delete_task(client: AsyncClient, sign_in):
    ctx = await _bootstrap(client, sign_in)
    task = (
        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Throwaway",
                "project_public_id": ctx["project"]["public_id"],
            },
        )
    ).json()

    r = await client.delete(f"/api/v1/tasks/{task['public_id']}")
    assert r.status_code == 204

    listing = await client.get("/api/v1/tasks")
    assert all(t["public_id"] != task["public_id"] for t in listing.json())

    listing_with_deleted = await client.get(
        "/api/v1/tasks", params={"include_deleted": "true"}
    )
    deleted = next(t for t in listing_with_deleted.json() if t["public_id"] == task["public_id"])
    assert deleted["deleted_at"] is not None


@pytest.mark.asyncio
async def test_comments_on_task(client: AsyncClient, sign_in):
    ctx = await _bootstrap(client, sign_in)
    task = (
        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Talk to coach",
                "project_public_id": ctx["project"]["public_id"],
            },
        )
    ).json()

    create = await client.post(
        f"/api/v1/tasks/{task['public_id']}/comments",
        json={"text": "Will call Monday"},
    )
    assert create.status_code == 201

    listing = await client.get(f"/api/v1/tasks/{task['public_id']}/comments")
    comments = listing.json()
    assert len(comments) == 1
    assert comments[0]["text"] == "Will call Monday"
