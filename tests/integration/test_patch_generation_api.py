"""Integration tests for Phase 5: Patch Generation & Candidate Validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest
from app.ai.client import AIProvider, AIProviderError, AIResponse
from app.api.dependencies import get_ai_provider_dep
from app.main import app
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


async def setup_proven_regression_investigation(
    async_client: AsyncClient,
) -> tuple[str, bytes]:
    """Helper creating an investigation with proven regression test in VERIFYING state."""
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
    reproduce_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert reproduce_resp.status_code == 200
    assert reproduce_resp.json()["status"] == "REPRODUCED"

    # 4. Formulate causal hypothesis
    hyp_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/investigate")
    assert hyp_resp.status_code == 200

    # 5. Generate and verify regression test (transitions to VERIFYING)
    reg_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/regression-test"
    )
    assert reg_resp.status_code == 200
    assert reg_resp.json()["verification_status"] == "REGRESSION_PROVEN"

    # Verify investigation status is VERIFYING
    get_inv = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_inv.json()["status"] == "VERIFYING"

    return inv_id, broken_bytes


@pytest.mark.asyncio
async def test_patch_generation_happy_path(async_client: AsyncClient) -> None:
    """Complete Phase 5 end-to-end integration flow:

    proven regression in VERIFYING -> generate patch -> validate unified diff ->
    confirm PATCH_VALIDATED and NOT_VERIFIED -> verify repository remains unpatched ->
    lifecycle remains VERIFYING.
    """
    inv_id, original_bytes = await setup_proven_regression_investigation(async_client)
    original_sha256 = hashlib.sha256(original_bytes).hexdigest()

    # 1. Generate candidate patch
    patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
    assert patch_resp.status_code == 200
    data = patch_resp.json()

    assert data["investigation_id"] == inv_id
    assert data["status"] == "VALIDATED"
    assert data["verification_status"] == "NOT_VERIFIED"
    assert data["validation_result"] == "VALID"
    assert data["patch_format"] == "unified_diff"
    assert data["changed_files"] == ["src/calculator.py"]
    assert "--- a/src/calculator.py" in data["patch_content"]
    assert "+++ b/src/calculator.py" in data["patch_content"]
    assert "+    return a / b" in data["patch_content"]
    assert data["prompt_version"] == "evida-patch-generation-v1"
    assert data["created_at"] is not None
    assert data["validated_at"] is not None

    # 2. Lifecycle must remain in VERIFYING (not COMPLETED or FIXED)
    inv_check = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert inv_check.json()["status"] == "VERIFYING"

    # 3. Retrieve patch via GET endpoint
    get_patch_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/patch")
    assert get_patch_resp.status_code == 200
    assert get_patch_resp.json()["id"] == data["id"]
    assert get_patch_resp.json()["status"] == "VALIDATED"
    assert get_patch_resp.json()["verification_status"] == "NOT_VERIFIED"

    # 4. Idempotency: repeated POST returns existing validated patch
    idempotent_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
    assert idempotent_resp.status_code == 200
    assert idempotent_resp.json()["id"] == data["id"]

    # 5. Audit Events
    events_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/events")
    assert events_resp.status_code == 200
    event_types = [e["event_type"] for e in events_resp.json()["items"]]
    assert "PATCH_GENERATION_STARTED" in event_types
    assert "PATCH_GENERATED" in event_types
    assert "PATCH_VALIDATED" in event_types

    # 6. Source Integrity Test: Repository archive must remain completely unchanged
    repo_meta = await async_client.get(f"/api/v1/investigations/{inv_id}/repository")
    assert repo_meta.status_code == 200
    assert repo_meta.json()["archive_sha256"] == original_sha256


@pytest.mark.asyncio
async def test_patch_precondition_failures(async_client: AsyncClient) -> None:
    """Preconditions: cannot generate patch without VERIFYING status and proven regression."""
    # 1. Fresh investigation (status CREATED)
    create_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Fresh investigation",
            "bug_description": "Testing preconditions.",
        },
    )
    inv_id = create_resp.json()["id"]

    patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
    assert patch_resp.status_code == 400
    assert patch_resp.json()["error"]["code"] == "PATCH_PRECONDITION_FAILED"

    # 2. Get patch when none exists yields 404
    get_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/patch")
    assert get_resp.status_code == 404
    assert get_resp.json()["error"]["code"] == "PATCH_CANDIDATE_NOT_FOUND"


@pytest.mark.asyncio
async def test_patch_rejection_test_modification(async_client: AsyncClient) -> None:
    """When the AI proposes a patch that modifies test files, it must be rejected with TEST_MODIFICATION."""
    inv_id, _ = await setup_proven_regression_investigation(async_client)

    test_mod_patch_json = json.dumps(
        {
            "description": "Weaken the regression test to make it pass",
            "patch_format": "unified_diff",
            "patch_content": (
                "--- a/tests/test_regression.py\n"
                "+++ b/tests/test_regression.py\n"
                "@@ -1,2 +1,2 @@\n"
                "-    assert divide(10, 2) == 5\n"
                "+    assert True\n"
            ),
            "changed_files": ["tests/test_regression.py"],
            "change_summary": [
                {"file": "tests/test_regression.py", "reason": "Change assertion"}
            ],
            "reasoning": "Disable test assertion",
        }
    )

    class TestModMockProvider(AIProvider):
        @property
        def provider_name(self) -> str:
            return "mock"

        async def generate(
            self, *, system_prompt: str, user_prompt: str, **kwargs
        ) -> AIResponse:
            return AIResponse(
                content=test_mod_patch_json,
                model="mock-nemotron",
                provider="mock",
                duration_ms=5.0,
            )

    fastapi_app = getattr(async_client._transport, "app", app)
    fastapi_app.dependency_overrides[get_ai_provider_dep] = lambda: (
        TestModMockProvider()
    )

    try:
        patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
        assert patch_resp.status_code == 400
        assert patch_resp.json()["error"]["code"] == "TEST_MODIFICATION"

        # Verify audit event PATCH_REJECTED was recorded
        events_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/events")
        event_types = [e["event_type"] for e in events_resp.json()["items"]]
        assert "PATCH_REJECTED" in event_types
    finally:
        fastapi_app.dependency_overrides.pop(get_ai_provider_dep, None)


@pytest.mark.asyncio
async def test_patch_rejection_path_traversal(async_client: AsyncClient) -> None:
    """When the AI proposes a patch with path traversal, it is rejected with PATH_VIOLATION."""
    inv_id, _ = await setup_proven_regression_investigation(async_client)

    traversal_patch_json = json.dumps(
        {
            "description": "Path traversal attempt",
            "patch_format": "unified_diff",
            "patch_content": (
                "--- a/../etc/passwd\n"
                "+++ b/../etc/passwd\n"
                "@@ -1,1 +1,1 @@\n"
                "-root:x:0:0\n"
                "+root:x:0:0:hacked\n"
            ),
            "changed_files": ["../etc/passwd"],
            "change_summary": [{"file": "../etc/passwd", "reason": "Traversal"}],
            "reasoning": "Escape workspace",
        }
    )

    class TraversalMockProvider(AIProvider):
        @property
        def provider_name(self) -> str:
            return "mock"

        async def generate(
            self, *, system_prompt: str, user_prompt: str, **kwargs
        ) -> AIResponse:
            return AIResponse(
                content=traversal_patch_json,
                model="mock-nemotron",
                provider="mock",
                duration_ms=5.0,
            )

    fastapi_app = getattr(async_client._transport, "app", app)
    fastapi_app.dependency_overrides[get_ai_provider_dep] = lambda: (
        TraversalMockProvider()
    )

    try:
        patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
        assert patch_resp.status_code == 400
        assert patch_resp.json()["error"]["code"] == "PATH_VIOLATION"
    finally:
        fastapi_app.dependency_overrides.pop(get_ai_provider_dep, None)


@pytest.mark.asyncio
async def test_patch_rejection_sensitive_file(async_client: AsyncClient) -> None:
    """When the AI proposes a patch targeting sensitive files, it is rejected with SENSITIVE_FILE_MODIFICATION."""
    inv_id, _ = await setup_proven_regression_investigation(async_client)

    sensitive_patch_json = json.dumps(
        {
            "description": "Sensitive file modification",
            "patch_format": "unified_diff",
            "patch_content": (
                "--- a/.env\n+++ b/.env\n@@ -1,1 +1,1 @@\n-SECRET=1\n+SECRET=2\n"
            ),
            "changed_files": [".env"],
            "change_summary": [{"file": ".env", "reason": "Modify secret"}],
            "reasoning": "Expose secrets",
        }
    )

    class SensitiveMockProvider(AIProvider):
        @property
        def provider_name(self) -> str:
            return "mock"

        async def generate(
            self, *, system_prompt: str, user_prompt: str, **kwargs
        ) -> AIResponse:
            return AIResponse(
                content=sensitive_patch_json,
                model="mock-nemotron",
                provider="mock",
                duration_ms=5.0,
            )

    fastapi_app = getattr(async_client._transport, "app", app)
    fastapi_app.dependency_overrides[get_ai_provider_dep] = lambda: (
        SensitiveMockProvider()
    )

    try:
        patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
        assert patch_resp.status_code == 400
        assert patch_resp.json()["error"]["code"] == "SENSITIVE_FILE_MODIFICATION"
    finally:
        fastapi_app.dependency_overrides.pop(get_ai_provider_dep, None)


@pytest.mark.asyncio
async def test_patch_rejection_security_violation(async_client: AsyncClient) -> None:
    """When the AI proposes a patch introducing dangerous calls, it is rejected with SECURITY_VIOLATION."""
    inv_id, _ = await setup_proven_regression_investigation(async_client)

    danger_patch_json = json.dumps(
        {
            "description": "Dangerous subprocess patch",
            "patch_format": "unified_diff",
            "patch_content": (
                "--- a/src/calculator.py\n"
                "+++ b/src/calculator.py\n"
                "@@ -1,2 +1,3 @@\n"
                " def divide(a, b):\n"
                "+    import subprocess; subprocess.Popen(['ls'])\n"
                "     return a / b\n"
            ),
            "changed_files": ["src/calculator.py"],
            "change_summary": [
                {"file": "src/calculator.py", "reason": "Inject subprocess"}
            ],
            "reasoning": "Spawn process",
        }
    )

    class DangerMockProvider(AIProvider):
        @property
        def provider_name(self) -> str:
            return "mock"

        async def generate(
            self, *, system_prompt: str, user_prompt: str, **kwargs
        ) -> AIResponse:
            return AIResponse(
                content=danger_patch_json,
                model="mock-nemotron",
                provider="mock",
                duration_ms=5.0,
            )

    fastapi_app = getattr(async_client._transport, "app", app)
    fastapi_app.dependency_overrides[get_ai_provider_dep] = lambda: DangerMockProvider()

    try:
        patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
        assert patch_resp.status_code == 400
        assert patch_resp.json()["error"]["code"] == "SECURITY_VIOLATION"
    finally:
        fastapi_app.dependency_overrides.pop(get_ai_provider_dep, None)


@pytest.mark.asyncio
async def test_patch_rejection_out_of_scope(async_client: AsyncClient) -> None:
    """When the AI proposes a patch modifying an unrelated file outside confirmed scope, it is rejected."""
    inv_id, _ = await setup_proven_regression_investigation(async_client)

    out_of_scope_json = json.dumps(
        {
            "description": "Out of scope modification",
            "patch_format": "unified_diff",
            "patch_content": (
                "--- a/src/__init__.py\n"
                "+++ b/src/__init__.py\n"
                "@@ -1,0 +1,1 @@\n"
                "+# unrelated comment\n"
            ),
            "changed_files": ["src/__init__.py"],
            "change_summary": [{"file": "src/__init__.py", "reason": "Edit init file"}],
            "reasoning": "Unrelated edit outside affected files",
        }
    )

    class OutOfScopeMockProvider(AIProvider):
        @property
        def provider_name(self) -> str:
            return "mock"

        async def generate(
            self, *, system_prompt: str, user_prompt: str, **kwargs
        ) -> AIResponse:
            return AIResponse(
                content=out_of_scope_json,
                model="mock-nemotron",
                provider="mock",
                duration_ms=5.0,
            )

    fastapi_app = getattr(async_client._transport, "app", app)
    fastapi_app.dependency_overrides[get_ai_provider_dep] = lambda: (
        OutOfScopeMockProvider()
    )

    try:
        patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
        assert patch_resp.status_code == 400
        assert patch_resp.json()["error"]["code"] == "OUT_OF_SCOPE_CHANGE"
    finally:
        fastapi_app.dependency_overrides.pop(get_ai_provider_dep, None)


@pytest.mark.asyncio
async def test_patch_ai_provider_failure(async_client: AsyncClient) -> None:
    """When the AI provider throws an AIProviderError, 503 AI_PROVIDER_UNAVAILABLE is returned."""
    inv_id, _ = await setup_proven_regression_investigation(async_client)

    class FailingAIProvider(AIProvider):
        @property
        def provider_name(self) -> str:
            return "failing"

        async def generate(
            self, *, system_prompt: str, user_prompt: str, **kwargs
        ) -> AIResponse:
            raise AIProviderError("Nebius 503 Service Unavailable", status_code=503)

    fastapi_app = getattr(async_client._transport, "app", app)
    fastapi_app.dependency_overrides[get_ai_provider_dep] = lambda: FailingAIProvider()

    try:
        patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
        assert patch_resp.status_code == 503
        assert patch_resp.json()["error"]["code"] == "AI_PROVIDER_UNAVAILABLE"
    finally:
        fastapi_app.dependency_overrides.pop(get_ai_provider_dep, None)
