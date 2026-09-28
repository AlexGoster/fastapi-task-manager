"""Tests for task routes."""

import pytest
from httpx import AsyncClient

from app.tests.conftest import token_for


async def test_create_task(client: AsyncClient, token_for):
    token = await token_for(client)
    resp = await client.post("/tasks/", json={"title": "Test task", "priority": "high"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "Test task"


async def test_list_tasks(client: AsyncClient, token_for):
    token = await token_for(client)
    await client.post("/tasks/", json={"title": "Task A", "priority": "low"}, headers={"Authorization": f"Bearer {token}"})
    resp = await client.get("/tasks/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


async def test_filter_by_status(client: AsyncClient, token_for):
    token = await token_for(client)
    await client.post("/tasks/", json={"title": "Done task", "status": "done"}, headers={"Authorization": f"Bearer {token}"})
    await client.post("/tasks/", json={"title": "Pending task", "status": "pending"}, headers={"Authorization": f"Bearer {token}"})
    resp = await client.get("/tasks/?status_filter=done", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["title"] == "Done task"


async def test_filter_by_priority(client: AsyncClient, token_for):
    token = await token_for(client)
    await client.post("/tasks/", json={"title": "High task", "priority": "high"}, headers={"Authorization": f"Bearer {token}"})
    resp = await client.get("/tasks/?priority_filter=high", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["priority"] == "high"


async def test_get_task(client: AsyncClient, token_for):
    token = await token_for(client)
    create = await client.post("/tasks/", json={"title": "Get me"}, headers={"Authorization": f"Bearer {token}"})
    task_id = create.json()["id"]
    resp = await client.get(f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Get me"


async def test_update_task(client: AsyncClient, token_for):
    token = await token_for(client)
    create = await client.post("/tasks/", json={"title": "Update me"}, headers={"Authorization": f"Bearer {token}"})
    task_id = create.json()["id"]
    resp = await client.put(f"/tasks/{task_id}", json={"status": "done"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


async def test_delete_task(client: AsyncClient, token_for):
    token = await token_for(client)
    create = await client.post("/tasks/", json={"title": "Delete me"}, headers={"Authorization": f"Bearer {token}"})
    task_id = create.json()["id"]
    resp = await client.delete(f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204
    get = await client.get(f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert get.status_code == 404


async def test_unauthorized_access(client: AsyncClient):
    resp = await client.post("/tasks/", json={"title": "No auth"})
    assert resp.status_code == 401


async def test_pagination(client: AsyncClient, token_for):
    token = await token_for(client)
    for i in range(25):
        await client.post("/tasks/", json={"title": f"Task {i}"}, headers={"Authorization": f"Bearer {token}"})
    resp = await client.get("/tasks/?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 10
    assert resp.json()["total"] == 25
    assert resp.json()["pages"] == 3


async def test_create_task_invalid_priority(client: AsyncClient, token_for):
    token = await token_for(client)
    resp = await client.post("/tasks/", json={"title": "Bad", "priority": "invalid"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 422


async def test_create_task_empty_title(client: AsyncClient, token_for):
    token = await token_for(client)
    resp = await client.post("/tasks/", json={"title": ""}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 422