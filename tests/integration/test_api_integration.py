"""Integration tests for FastAPI application and error envelopes."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_full_health_lifecycle(async_client: AsyncClient):
    # Liveness probe
    health_resp = await async_client.get("/api/v1/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"

    # Readiness probe
    ready_resp = await async_client.get("/api/v1/health/ready")
    assert ready_resp.status_code == 200
    assert "checks" in ready_resp.json()

    # Investigations endpoint
    inv_resp = await async_client.get("/api/v1/investigations")
    assert inv_resp.status_code == 200
    assert "items" in inv_resp.json()


@pytest.mark.asyncio
async def test_standardized_error_envelope(async_client: AsyncClient):
    # 404 Not Found returns standardized error envelope
    resp = await async_client.get("/api/v1/nonexistent-endpoint")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "request_id" in data["error"]
