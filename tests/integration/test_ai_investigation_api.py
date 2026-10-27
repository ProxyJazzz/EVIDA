"""Integration tests for Phase 3: AI Investigation & Hypothesis Engine."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from app.ai.client import AIProvider, AIResponse
from app.api.dependencies import get_ai_provider_dep
from app.main import app
from httpx import AsyncClient

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
BROKEN_REPO_ZIP = FIXTURES_DIR / "broken_python_repo.zip"
PASSING_REPO_ZIP = FIXTURES_DIR / "passing_python_repo.zip"


@pytest.fixture(autouse=True)
def ensure_fixtures_exist() -> None:
    """Ensure fixture archives are created before tests execute."""
    if not BROKEN_REPO_ZIP.exists() or not PASSING_REPO_ZIP.exists():
        from tests.fixtures.generate_fixtures import (
            create_broken_repo_zip,
            create_passing_repo_zip,
        )

        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        create_broken_repo_zip()
        create_passing_repo_zip()


@pytest.mark.asyncio
async def test_ai_investigation_happy_path(async_client: AsyncClient) -> None:
    """End-to-end happy path:

    Create investigation -> upload broken repo -> reproduce failure ->
    POST /investigate -> verify status INVESTIGATING & hypothesis persisted ->
    GET /hypothesis returns the persisted structured hypothesis.
    """
    repo_id = str(uuid4())
    proj_id = str(uuid4())

    # 1. Create Investigation
    create_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "project_id": proj_id,
            "repository_id": repo_id,
            "title": "Fix calculator division bug",
            "bug_description": "divide(10, 2) returns 20 instead of 5.",
        },
    )
    assert create_resp.status_code == 201
    inv_id = create_resp.json()["id"]

    # 2. Upload broken repository ZIP
    broken_bytes = BROKEN_REPO_ZIP.read_bytes()
    upload_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={"file": ("broken_python_repo.zip", broken_bytes, "application/zip")},
    )
    assert upload_resp.status_code == 201

    # 3. Execute failure reproduction command
    reproduce_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert reproduce_resp.status_code == 200
    assert reproduce_resp.json()["status"] == "REPRODUCED"

    # Verify status is REPRODUCING
    get_inv_repro = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_inv_repro.json()["status"] == "REPRODUCING"

    # 4. Trigger AI investigation
    investigate_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/investigate"
    )
    assert investigate_resp.status_code == 200
    hyp_data = investigate_resp.json()

    assert hyp_data["investigation_id"] == inv_id
    assert hyp_data["provider"] == "mock"
    assert (
        "nvidia" in hyp_data["model"].lower() or "nemotron" in hyp_data["model"].lower()
    )
    assert hyp_data["prompt_version"] == "evida-investigation-v1"
    assert (
        "divide" in hyp_data["hypothesis"].lower()
        or "multiplies" in hyp_data["hypothesis"].lower()
    )
    assert 0.0 <= hyp_data["confidence"] <= 1.0

    # Root cause candidate verification
    root_cause = hyp_data["root_cause"]
    assert "calculator.py" in root_cause["file"]
    assert root_cause["symbol"] == "divide"
    assert root_cause["line"] > 0
    assert root_cause["description"]

    assert len(hyp_data["affected_files"]) > 0
    assert "src/calculator.py" in hyp_data["affected_files"]
    assert len(hyp_data["evidence"]) > 0
    assert hyp_data["recommended_next_action"] == "generate_regression_test"

    # 5. Verify Investigation transitioned: REPRODUCING -> INVESTIGATING
    get_inv_after = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_inv_after.json()["status"] == "INVESTIGATING"

    # 6. Retrieve hypothesis via GET endpoint
    get_hyp_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/hypothesis")
    assert get_hyp_resp.status_code == 200
    assert get_hyp_resp.json()["id"] == hyp_data["id"]
    assert get_hyp_resp.json()["hypothesis"] == hyp_data["hypothesis"]
    assert get_hyp_resp.json()["confidence"] == hyp_data["confidence"]
    assert get_hyp_resp.json()["root_cause"] == hyp_data["root_cause"]

    # 7. Test Idempotency: repeated investigate call returns existing hypothesis
    idempotent_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/investigate"
    )
    assert idempotent_resp.status_code == 200
    assert idempotent_resp.json()["id"] == hyp_data["id"]

    # 8. Verify event timeline includes Phase 3 audit event
    events_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/events")
    assert events_resp.status_code == 200
    event_types = [e["event_type"] for e in events_resp.json()["items"]]
    assert "INVESTIGATION_HYPOTHESIS_RECORDED" in event_types


@pytest.mark.asyncio
async def test_investigate_fails_if_not_reproduced(async_client: AsyncClient) -> None:
    """If reproduction status is NOT_REPRODUCED, investigation must fail with 400."""
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Passing test repo",
            "bug_description": "Everything works as expected.",
        },
    )
    inv_id = inv_resp.json()["id"]

    passing_bytes = PASSING_REPO_ZIP.read_bytes()
    await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={"file": ("passing_python_repo.zip", passing_bytes, "application/zip")},
    )

    repro_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert repro_resp.json()["status"] == "NOT_REPRODUCED"

    # Attempt AI investigation on non-reproduced bug
    investigate_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/investigate"
    )
    assert investigate_resp.status_code == 400
    err = investigate_resp.json()["error"]
    assert err["code"] == "INVESTIGATION_PRECONDITION_FAILED"
    assert "NOT_REPRODUCED" in err["message"]


@pytest.mark.asyncio
async def test_investigate_fails_without_reproduction(
    async_client: AsyncClient,
) -> None:
    """Cannot investigate without a reproduction run."""
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "No reproduction run",
            "bug_description": "Never reproduced.",
        },
    )
    inv_id = inv_resp.json()["id"]

    investigate_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/investigate"
    )
    assert investigate_resp.status_code == 400
    err = investigate_resp.json()["error"]
    assert err["code"] == "INVESTIGATION_PRECONDITION_FAILED"


@pytest.mark.asyncio
async def test_get_hypothesis_not_found(async_client: AsyncClient) -> None:
    """GET /hypothesis returns 404 HYPOTHESIS_NOT_FOUND when none has been recorded."""
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Empty hypothesis test",
            "bug_description": "No hypothesis yet.",
        },
    )
    inv_id = inv_resp.json()["id"]

    get_hyp_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/hypothesis")
    assert get_hyp_resp.status_code == 404
    err = get_hyp_resp.json()["error"]
    assert err["code"] == "HYPOTHESIS_NOT_FOUND"


@pytest.mark.asyncio
async def test_investigate_handles_malformed_ai_response(
    async_client: AsyncClient,
) -> None:
    """When the AI provider returns unparseable content, it returns 502 AI_RESPONSE_INVALID."""
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Malformed AI response test",
            "bug_description": "Bug to test invalid AI output.",
        },
    )
    inv_id = inv_resp.json()["id"]

    broken_bytes = BROKEN_REPO_ZIP.read_bytes()
    await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={"file": ("broken_python_repo.zip", broken_bytes, "application/zip")},
    )
    await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )

    class MalformedAIProvider(AIProvider):
        @property
        def provider_name(self) -> str:
            return "broken_mock"

        async def generate(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            temperature: float = 0.2,
            max_tokens: int = 2048,
        ) -> AIResponse:
            return AIResponse(
                content="I am not returning JSON, just random text: lol oops",
                model="broken-model",
                provider="broken_mock",
                duration_ms=12.5,
            )

    fastapi_app = getattr(async_client._transport, "app", app)
    fastapi_app.dependency_overrides[get_ai_provider_dep] = lambda: (
        MalformedAIProvider()
    )

    try:
        investigate_resp = await async_client.post(
            f"/api/v1/investigations/{inv_id}/investigate"
        )
        assert investigate_resp.status_code == 502
        err = investigate_resp.json()["error"]
        assert err["code"] == "AI_RESPONSE_INVALID"
    finally:
        fastapi_app.dependency_overrides.pop(get_ai_provider_dep, None)
