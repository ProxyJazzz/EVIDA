"""Integration tests for Phase 7: Evidence Bundle, Provenance & Audit System."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest
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


async def setup_verified_investigation(async_client: AsyncClient) -> str:
    """Helper creating a fully verified investigation (Phases 1-6)."""
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

    # 3. Reproduce failure
    repro_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert repro_resp.status_code == 200

    # 4. Formulate causal hypothesis
    hyp_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/investigate")
    assert hyp_resp.status_code == 200

    # 5. Generate and prove regression test
    reg_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/regression-test"
    )
    assert reg_resp.status_code == 200

    # 6. Generate and validate candidate patch
    patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
    assert patch_resp.status_code == 200

    # 7. Execute double validation
    verify_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/verify-patch"
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verdict"] == "VERIFIED"

    return inv_id


@pytest.mark.asyncio
async def test_get_evidence_bundle_happy_path(async_client: AsyncClient) -> None:
    """Full end-to-end evidence bundle retrieval and validation."""
    inv_id = await setup_verified_investigation(async_client)

    # 1. GET /api/v1/investigations/{id}/evidence
    ev_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence")
    assert ev_resp.status_code == 200
    bundle = ev_resp.json()

    assert bundle["investigation_id"] == inv_id
    assert bundle["verdict"] == "VERIFIED"
    assert len(bundle["bundle_sha256"]) == 64
    assert len(bundle["evidence_items"]) >= 10

    # Check that individual phases are recorded
    types = [item["evidence_type"] for item in bundle["evidence_items"]]
    assert "INCIDENT" in types
    assert "REPOSITORY" in types
    assert "REPRODUCTION" in types
    assert "HYPOTHESIS" in types
    assert "REGRESSION_TEST" in types
    assert "REGRESSION_PROOF" in types
    assert "PATCH_PROPOSAL" in types
    assert "PATCH_VALIDATION" in types
    assert "PATCH_APPLICATION" in types
    assert "REGRESSION_VERIFICATION" in types
    assert "BASELINE_VERIFICATION" in types
    assert "SOURCE_INTEGRITY" in types
    assert "FINAL_VERDICT" in types

    # Check provenance segregation: AI proposals vs deterministic evidence
    hypo_item = next(
        i for i in bundle["evidence_items"] if i["evidence_type"] == "HYPOTHESIS"
    )
    assert hypo_item["provenance"] == "AI_PROPOSAL"

    reg_item = next(
        i
        for i in bundle["evidence_items"]
        if i["evidence_type"] == "REGRESSION_VERIFICATION"
    )
    assert reg_item["provenance"] == "DETERMINISTIC_EXECUTION"

    source_item = next(
        i for i in bundle["evidence_items"] if i["evidence_type"] == "SOURCE_INTEGRITY"
    )
    assert source_item["provenance"] == "CRYPTOGRAPHIC_INTEGRITY"

    # 2. GET /api/v1/investigations/{id}/evidence/items
    items_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/evidence/items"
    )
    assert items_resp.status_code == 200
    items = items_resp.json()
    assert len(items) == len(bundle["evidence_items"])

    # 3. GET /api/v1/investigations/{id}/evidence/hash
    hash_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/hash")
    assert hash_resp.status_code == 200
    hash_data = hash_resp.json()
    assert hash_data["bundle_sha256"] == bundle["bundle_sha256"]
    assert hash_data["investigation_id"] == inv_id

    # 4. GET /api/v1/investigations/{id}/evidence/export
    export_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/evidence/export"
    )
    assert export_resp.status_code == 200
    assert "attachment" in export_resp.headers.get("content-disposition", "")
    assert f"evida-evidence-{inv_id}.json" in export_resp.headers.get(
        "content-disposition", ""
    )
    exported_data = json.loads(export_resp.text)
    assert exported_data["bundle_sha256"] == bundle["bundle_sha256"]
    assert exported_data["verdict"] == "VERIFIED"

    # 5. Check Audit events emitted
    events_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/events")
    assert events_resp.status_code == 200
    event_types = [e["event_type"] for e in events_resp.json()["items"]]
    assert "EVIDENCE_BUNDLE_GENERATED" in event_types
    assert "EVIDENCE_BUNDLE_EXPORTED" in event_types


@pytest.mark.asyncio
async def test_evidence_api_tenant_isolation(async_client: AsyncClient) -> None:
    """User B must be forbidden from accessing User A's evidence bundle."""
    headers_a = {"Authorization": "Bearer tenant_a_token"}
    headers_b = {"Authorization": "Bearer tenant_b_token"}

    # User A creates investigation
    create_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "project_id": str(uuid4()),
            "repository_id": str(uuid4()),
            "title": "Confidential Security Fix",
            "bug_description": "Proprietary algorithm defect",
        },
        headers=headers_a,
    )
    assert create_resp.status_code == 201
    inv_id = create_resp.json()["id"]

    # User B attempts to access evidence bundle
    resp_bundle = await async_client.get(
        f"/api/v1/investigations/{inv_id}/evidence", headers=headers_b
    )
    assert resp_bundle.status_code == 403

    # User B attempts to access evidence items
    resp_items = await async_client.get(
        f"/api/v1/investigations/{inv_id}/evidence/items", headers=headers_b
    )
    assert resp_items.status_code == 403

    # User B attempts to access bundle hash
    resp_hash = await async_client.get(
        f"/api/v1/investigations/{inv_id}/evidence/hash", headers=headers_b
    )
    assert resp_hash.status_code == 403

    # User B attempts export
    resp_export = await async_client.get(
        f"/api/v1/investigations/{inv_id}/evidence/export", headers=headers_b
    )
    assert resp_export.status_code == 403


@pytest.mark.asyncio
async def test_evidence_api_xss_and_secret_scrubbing(async_client: AsyncClient) -> None:
    """Evidence payloads must scrub credentials and safely store untrusted XSS strings."""
    create_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "project_id": str(uuid4()),
            "repository_id": str(uuid4()),
            "title": "Bug with <script>alert('xss')</script>",
            "bug_description": "Failed with NEBIUS_API_KEY=secret_key_to_scrub_999",
        },
    )
    assert create_resp.status_code == 201
    inv_id = create_resp.json()["id"]

    ev_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence")
    assert ev_resp.status_code == 200
    bundle = ev_resp.json()

    # Secret was scrubbed
    bundle_str = json.dumps(bundle)
    assert "secret_key_to_scrub_999" not in bundle_str
    assert "[SCRUBBED_SECRET]" in bundle_str

    # XSS string is captured verbatim as data without executing
    incident_item = next(
        i for i in bundle["evidence_items"] if i["evidence_type"] == "INCIDENT"
    )
    assert "<script>alert('xss')</script>" in incident_item["data"]["title"]
