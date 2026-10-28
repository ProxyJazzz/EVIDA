"""Full End-to-End Acceptance and Regression Tests (Phase 8).

Validates:
1. Complete happy path: from fresh investigation to double-verified COMPLETED repair and evidence bundle.
2. Negative path: invalid patch leads to UNVERIFIED verdict and status remains VERIFYING.
3. Multi-tenant authorization: User A's artifacts are inaccessible to User B across all endpoints (403).
4. Anonymous rejection in production: requests without Authorization header are rejected (401).
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest
from app.core.config import get_settings
from app.domain.investigations.models import InvestigationStatus
from httpx import AsyncClient

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
BROKEN_REPO_ZIP = FIXTURES_DIR / "broken_python_repo.zip"


@pytest.fixture(autouse=True)
def ensure_fixtures_exist() -> None:
    """Ensure fixture archives are created before tests execute."""
    if not BROKEN_REPO_ZIP.exists():
        from tests.fixtures.generate_fixtures import create_broken_repo_zip

        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        create_broken_repo_zip()


@pytest.mark.asyncio
async def test_full_e2e_successful_repair_workflow(async_client: AsyncClient) -> None:
    """Exercises the complete canonical repair workflow:

    Upload -> Reproduce -> Hypothesize -> Prove Regression -> Validate Patch ->
    Double Verification -> VERIFIED -> Evidence Bundle Export.
    """
    proj_id = str(uuid4())
    repo_id = str(uuid4())

    # 1. Create Investigation
    create_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "project_id": proj_id,
            "repository_id": repo_id,
            "title": "Fix calculator division bug",
            "bug_description": "divide(10, 2) evaluates to 20 instead of 5.",
        },
    )
    assert create_resp.status_code == 201
    inv_data = create_resp.json()
    inv_id = inv_data["id"]
    assert inv_data["status"] == InvestigationStatus.CREATED

    # 2. Upload Repository Archive
    broken_bytes = BROKEN_REPO_ZIP.read_bytes()
    upload_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={"file": ("broken_python_repo.zip", broken_bytes, "application/zip")},
    )
    assert upload_resp.status_code == 201
    repo_data = upload_resp.json()
    assert repo_data["status"] == "READY"
    assert repo_data["archive_size_bytes"] > 0
    assert len(repo_data["archive_sha256"]) == 64

    # 3. Reproduce Failure in Sandbox
    repro_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert repro_resp.status_code == 200
    repro_data = repro_resp.json()
    assert repro_data["status"] == "REPRODUCED"
    assert repro_data["exit_code"] != 0
    assert "assert 20 == 5" in repro_data["stdout"]

    # 4. Formulate AI Causal Hypothesis
    hypo_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/investigate")
    assert hypo_resp.status_code == 200
    hypo_data = hypo_resp.json()
    assert hypo_data["provider"] in {"mock", "nebius"}
    assert hypo_data["confidence"] > 0.8
    assert "src/calculator.py" in hypo_data["affected_files"]
    assert hypo_data["root_cause"]["symbol"] == "divide"

    # 5. Generate and Deterministically Prove Regression Test
    reg_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/regression-test"
    )
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    assert reg_data["generation_status"] == "GENERATED"
    assert reg_data["verification_status"] == "REGRESSION_PROVEN"
    assert reg_data["verification"]["exit_code"] != 0
    assert reg_data["verification"]["failure_classification"] == "ASSERTION_FAILURE"

    # 6. Generate and Structurally Validate Candidate Patch
    patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
    assert patch_resp.status_code == 200
    patch_data = patch_resp.json()
    assert patch_data["status"] == "VALIDATED"
    assert patch_data["verification_status"] == "NOT_VERIFIED"
    assert "src/calculator.py" in patch_data["changed_files"]
    assert "--- a/src/calculator.py" in patch_data["patch_content"]

    # 7. Execute Double Validation in Ephemeral Sandbox (Phase 6)
    verify_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/verify-patch"
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["status"] == "VERIFIED"
    assert verify_data["verdict"] == "VERIFIED"
    assert verify_data["failure_classification"] is None
    assert verify_data["patch_application"]["status"] == "APPLIED"
    assert verify_data["patch_application"]["exit_code"] == 0
    assert verify_data["regression_execution"]["status"] == "PASSED"
    assert verify_data["regression_execution"]["exit_code"] == 0
    assert verify_data["baseline_execution"]["status"] == "PASSED"
    assert verify_data["baseline_execution"]["exit_code"] == 0
    assert verify_data["source_integrity_verified"] is True

    # 8. Verify State Machine Reached COMPLETED
    inv_get = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert inv_get.status_code == 200
    assert inv_get.json()["status"] == InvestigationStatus.COMPLETED

    # 9. Verify Evidence Bundle Generation & Export (Phase 7)
    bundle_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence")
    assert bundle_resp.status_code == 200
    bundle = bundle_resp.json()
    assert bundle["verdict"] == "VERIFIED"
    assert len(bundle["bundle_sha256"]) == 64
    assert len(bundle["evidence_items"]) >= 10

    # Fast hash check
    hash_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/hash")
    assert hash_resp.status_code == 200
    assert hash_resp.json()["bundle_sha256"] == bundle["bundle_sha256"]

    # Export download attachment
    export_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/evidence/export"
    )
    assert export_resp.status_code == 200
    assert "attachment" in export_resp.headers["content-disposition"]
    exported_data = json.loads(export_resp.text)
    assert exported_data["bundle_sha256"] == bundle["bundle_sha256"]


@pytest.mark.asyncio
async def test_full_e2e_negative_unverified_workflow(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercises the negative failure path via real sandbox execution:

    When candidate patch fails to fix the defect, the regression test fails post-patch,
    producing an authoritative UNVERIFIED verdict, leaving status in VERIFYING,
    and recording the defect in the Evidence Bundle.
    """
    proj_id = str(uuid4())
    repo_id = str(uuid4())

    create_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "project_id": proj_id,
            "repository_id": repo_id,
            "title": "Division bug with flawed patch",
            "bug_description": "divide(10, 2) returns 20 instead of 5.",
        },
    )
    inv_id = create_resp.json()["id"]

    await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={
            "file": (
                "broken_python_repo.zip",
                BROKEN_REPO_ZIP.read_bytes(),
                "application/zip",
            )
        },
    )
    await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    await async_client.post(f"/api/v1/investigations/{inv_id}/investigate")
    await async_client.post(f"/api/v1/investigations/{inv_id}/regression-test")

    # Mock the patch provider to return a patch that changes multiplication to subtraction (still fails regression)
    flawed_patch_json = json.dumps(
        {
            "description": "Flawed patch changing multiplication to subtraction",
            "patch_format": "unified_diff",
            "patch_content": "--- a/src/calculator.py\n+++ b/src/calculator.py\n@@ -1,3 +1,3 @@\n def divide(a: int, b: int) -> int:\n     # Bug: multiplication instead of division\n-    return a * b\n+    return a - b\n",
            "changed_files": ["src/calculator.py"],
            "change_summary": [
                {"file": "src/calculator.py", "reason": "Replace with subtraction"}
            ],
            "reasoning": "Attempting repair",
        }
    )

    from app.ai.client import MockAIProvider
    from app.ai.schemas import AIResponse

    async def mock_flawed_generate(*args: object, **kwargs: object) -> AIResponse:
        return AIResponse(
            content=flawed_patch_json,
            model="nvidia/Nemotron-3_5-Lightning",
            provider="nebius",
            duration_ms=10.0,
        )

    monkeypatch.setattr(MockAIProvider, "generate", mock_flawed_generate)

    patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
    assert patch_resp.status_code == 200

    # Now verify patch: it applies, but regression test divide(10, 2) == 5 STILL FAILS!
    verify_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/verify-patch"
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["status"] == "UNVERIFIED"
    assert verify_data["verdict"] == "UNVERIFIED"
    assert verify_data["failure_classification"] == "REGRESSION_STILL_FAILING"

    # Status must NOT be COMPLETED; must remain in VERIFYING
    inv_get = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert inv_get.json()["status"] == InvestigationStatus.VERIFYING

    # Evidence bundle must record UNVERIFIED
    bundle_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence")
    assert bundle_resp.status_code == 200
    assert bundle_resp.json()["verdict"] == "UNVERIFIED"


@pytest.mark.asyncio
async def test_tenant_isolation_across_all_endpoints(async_client: AsyncClient) -> None:
    """User B must be rejected with 403 when accessing User A's investigation."""
    headers_a = {"Authorization": "Bearer user_a_secret_token"}
    headers_b = {"Authorization": "Bearer user_b_secret_token"}

    # User A creates investigation
    create_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "project_id": str(uuid4()),
            "repository_id": str(uuid4()),
            "title": "User A Private Repair",
            "bug_description": "Secret vulnerability in proprietary repo.",
        },
        headers=headers_a,
    )
    assert create_resp.status_code == 201
    inv_id = create_resp.json()["id"]

    # User B is rejected from getting investigation
    get_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}", headers=headers_b
    )
    assert get_resp.status_code == 403

    # User B is rejected from getting events
    events_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/events", headers=headers_b
    )
    assert events_resp.status_code == 403

    # User B is rejected from uploading repository
    upload_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={
            "file": (
                "broken_python_repo.zip",
                BROKEN_REPO_ZIP.read_bytes(),
                "application/zip",
            )
        },
        headers=headers_b,
    )
    assert upload_resp.status_code == 403

    # User B is rejected from reproducing failure
    repro_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
        headers=headers_b,
    )
    assert repro_resp.status_code == 403

    # User B is rejected from evidence
    ev_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/evidence", headers=headers_b
    )
    assert ev_resp.status_code == 403


@pytest.mark.asyncio
async def test_anonymous_request_rejected_in_production(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """In production (APP_ENV=production), requests without Authorization header must return 401."""
    monkeypatch.setenv("APP_ENV", "production")
    # Clear settings cache so APP_ENV=production takes effect

    get_settings.cache_clear()  # type: ignore[attr-defined]

    try:
        # Create without Authorization header
        resp = await async_client.post(
            "/api/v1/investigations",
            json={
                "project_id": str(uuid4()),
                "repository_id": str(uuid4()),
                "title": "Anonymous Attempt in Production",
            },
        )
        assert resp.status_code == 401
        data = resp.json()
        assert data["error"]["code"] == "UNAUTHORIZED"
    finally:
        # Restore test environment
        monkeypatch.setenv("APP_ENV", "test")
        get_settings.cache_clear()  # type: ignore[attr-defined]
