"""Integration tests for Investigation Lifecycle API endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_investigation_lifecycle_api_full_flow(async_client: AsyncClient):
    repo_id = str(uuid4())
    proj_id = str(uuid4())

    # 1. Create Investigation
    create_payload = {
        "project_id": proj_id,
        "repository_id": repo_id,
        "title": "Fix memory leak in websocket session",
        "bug_description": "WebSocket connections fail to free buffers on disconnect.",
    }
    create_resp = await async_client.post("/api/v1/investigations", json=create_payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    inv_id = created_data["id"]
    assert created_data["status"] == "CREATED"
    assert created_data["title"] == "Fix memory leak in websocket session"
    assert created_data["repository_id"] == repo_id
    assert created_data["project_id"] == proj_id

    # 2. Retrieve Investigation by ID
    get_resp = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["id"] == inv_id
    assert get_data["status"] == "CREATED"

    # 3. Check Initial Event Timeline
    events_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/events")
    assert events_resp.status_code == 200
    events_data = events_resp.json()
    assert events_data["total"] == 1
    assert events_data["items"][0]["event_type"] == "INVESTIGATION_CREATED"
    assert events_data["items"][0]["from_status"] is None
    assert events_data["items"][0]["to_status"] == "CREATED"

    # 4. Start Investigation: CREATED -> INGESTING
    start_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/start")
    assert start_resp.status_code == 200
    started_data = start_resp.json()
    assert started_data["status"] == "INGESTING"

    # 5. Idempotent Start: Repeated call returns current state safely
    repeat_start_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/start"
    )
    assert repeat_start_resp.status_code == 200
    assert repeat_start_resp.json()["status"] == "INGESTING"

    # 6. Check Event Timeline after Start
    events_resp2 = await async_client.get(f"/api/v1/investigations/{inv_id}/events")
    assert events_resp2.status_code == 200
    events_data2 = events_resp2.json()
    assert events_data2["total"] == 2
    assert events_data2["items"][0]["event_type"] == "INVESTIGATION_CREATED"
    assert events_data2["items"][1]["event_type"] == "INVESTIGATION_STARTED"
    assert events_data2["items"][1]["from_status"] == "CREATED"
    assert events_data2["items"][1]["to_status"] == "INGESTING"

    # 7. List Investigations includes the new record
    list_resp = await async_client.get("/api/v1/investigations")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    ids = [item["id"] for item in list_data["items"]]
    assert inv_id in ids


@pytest.mark.asyncio
async def test_investigation_not_found_returns_error_envelope(
    async_client: AsyncClient,
):
    nonexistent_id = str(uuid4())
    resp = await async_client.get(f"/api/v1/investigations/{nonexistent_id}")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "INVESTIGATION_NOT_FOUND"
    assert "not found" in data["error"]["message"].lower()
    assert "request_id" in data["error"]

    # Start on nonexistent also returns 404
    start_resp = await async_client.post(
        f"/api/v1/investigations/{nonexistent_id}/start"
    )
    assert start_resp.status_code == 404
    assert start_resp.json()["error"]["code"] == "INVESTIGATION_NOT_FOUND"

    # Events on nonexistent also returns 404
    events_resp = await async_client.get(
        f"/api/v1/investigations/{nonexistent_id}/events"
    )
    assert events_resp.status_code == 404
    assert events_resp.json()["error"]["code"] == "INVESTIGATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_invalid_uuid_returns_validation_error(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/investigations/not-a-valid-uuid")
    assert resp.status_code == 422
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in data["error"]
