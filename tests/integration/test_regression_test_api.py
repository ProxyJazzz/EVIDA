"""Integration tests for Phase 4: Regression Test Generation & Verification."""

from __future__ import annotations

import json
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
async def test_regression_test_happy_path(async_client: AsyncClient) -> None:
    """Complete Phase 4 end-to-end integration flow:

    broken_repo -> reproduce failure -> hypothesis -> generate regression test ->
    execute in sandbox against unpatched repo -> observe assertion failure ->
    REGRESSION_PROVEN -> investigation transitions INVESTIGATING -> VERIFYING.
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

    # 3. Reproduce failure (verdict REPRODUCED)
    reproduce_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert reproduce_resp.status_code == 200
    assert reproduce_resp.json()["status"] == "REPRODUCED"

    # 4. Formulate causal hypothesis (transitions REPRODUCING -> INVESTIGATING)
    hyp_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/investigate")
    assert hyp_resp.status_code == 200
    assert hyp_resp.json()["investigation_id"] == inv_id

    # Verify status is INVESTIGATING
    get_inv_resp = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_inv_resp.json()["status"] == "INVESTIGATING"

    # 5. Generate and verify regression test
    reg_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/regression-test"
    )
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()

    assert reg_data["investigation_id"] == inv_id
    assert reg_data["test_path"] == "tests/test_regression.py"
    assert reg_data["framework"] == "pytest"
    assert reg_data["generation_status"] == "GENERATED"
    assert reg_data["verification_status"] == "REGRESSION_PROVEN"
    assert reg_data["prompt_version"] == "evida-regression-test-v1"

    # Verify sandbox execution evidence
    verification = reg_data["verification"]
    assert verification is not None
    assert verification["status"] == "REGRESSION_PROVEN"
    assert verification["failure_classification"] == "ASSERTION_FAILURE"
    assert verification["exit_code"] == 1
    assert (
        "FAILED tests/test_regression.py::test_divide_regression"
        in verification["stdout"]
    )
    assert "assert 20 == 5" in verification["stdout"]
    assert verification["duration_ms"] is not None and verification["duration_ms"] > 0
    assert verification["timed_out"] is False

    # 6. Verify Investigation transitioned: INVESTIGATING -> VERIFYING
    get_inv_after = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_inv_after.json()["status"] == "VERIFYING"

    # 7. Retrieve regression test via GET endpoint
    get_reg_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/regression-test"
    )
    assert get_reg_resp.status_code == 200
    assert get_reg_resp.json()["id"] == reg_data["id"]
    assert get_reg_resp.json()["verification_status"] == "REGRESSION_PROVEN"

    # 8. Test Idempotency: repeated POST returns existing proven test
    idempotent_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/regression-test"
    )
    assert idempotent_resp.status_code == 200
    assert idempotent_resp.json()["id"] == reg_data["id"]

    # 9. Verify event timeline includes Phase 4 audit events
    events_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/events")
    assert events_resp.status_code == 200
    event_types = [e["event_type"] for e in events_resp.json()["items"]]
    assert "REGRESSION_TEST_GENERATED" in event_types
    assert "REGRESSION_TEST_VERIFICATION_STARTED" in event_types
    assert "REGRESSION_TEST_VERIFICATION_COMPLETED" in event_types
    assert "REGRESSION_TEST_PROVEN" in event_types


@pytest.mark.asyncio
async def test_regression_test_passing_is_rejected(async_client: AsyncClient) -> None:
    """When the AI produces a test that passes against the buggy repository,

    the test must be classified as TEST_REJECTED and must NOT transition to VERIFYING.
    """
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Passing test rejection test",
            "bug_description": "Testing rejection of passing test.",
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
    await async_client.post(f"/api/v1/investigations/{inv_id}/investigate")

    # Mock provider returning a vacuous/passing test
    passing_test_json = json.dumps(
        {
            "test_path": "tests/test_regression.py",
            "framework": "pytest",
            "language": "python",
            "description": "Vacuous passing test",
            "test_content": "def test_vacuous_pass():\n    assert 1 == 1\n",
            "target_symbol": "divide",
            "target_file": "src/calculator.py",
            "expected_failure_reason": "Expected to fail but actually passes",
        }
    )

    class PassingTestMockProvider(AIProvider):
        @property
        def provider_name(self) -> str:
            return "mock"

        async def generate(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            temperature: float = 0.2,
            max_tokens: int = 2048,
        ) -> AIResponse:
            return AIResponse(
                content=passing_test_json,
                model="mock-nemotron",
                provider="mock",
                duration_ms=5.0,
            )

    fastapi_app = getattr(async_client._transport, "app", app)
    fastapi_app.dependency_overrides[get_ai_provider_dep] = lambda: (
        PassingTestMockProvider()
    )

    try:
        reg_resp = await async_client.post(
            f"/api/v1/investigations/{inv_id}/regression-test"
        )
        assert reg_resp.status_code == 200
        data = reg_resp.json()
        assert data["verification_status"] == "TEST_REJECTED"
        assert data["verification"]["failure_classification"] == "PASSING"
        assert data["verification"]["exit_code"] == 0

        # Investigation must NOT transition to VERIFYING (remains INVESTIGATING)
        inv_check = await async_client.get(f"/api/v1/investigations/{inv_id}")
        assert inv_check.json()["status"] == "INVESTIGATING"

        # Audit events must include REGRESSION_TEST_REJECTED
        events_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/events")
        event_types = [e["event_type"] for e in events_resp.json()["items"]]
        assert "REGRESSION_TEST_REJECTED" in event_types
    finally:
        fastapi_app.dependency_overrides.pop(get_ai_provider_dep, None)


@pytest.mark.asyncio
async def test_regression_test_import_error_is_execution_error(
    async_client: AsyncClient,
) -> None:
    """When the AI produces a test with an import error, it is classified as EXECUTION_ERROR."""
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Import error test",
            "bug_description": "Testing import error classification.",
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
    await async_client.post(f"/api/v1/investigations/{inv_id}/investigate")

    import_error_json = json.dumps(
        {
            "test_path": "tests/test_regression.py",
            "framework": "pytest",
            "language": "python",
            "description": "Test importing nonexistent module",
            "test_content": "import nonexistent_module_xyz\n\ndef test_dummy():\n    assert True\n",
            "target_symbol": "divide",
            "target_file": "src/calculator.py",
            "expected_failure_reason": "Module not found",
        }
    )

    class ImportErrorMockProvider(AIProvider):
        @property
        def provider_name(self) -> str:
            return "mock"

        async def generate(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            temperature: float = 0.2,
            max_tokens: int = 2048,
        ) -> AIResponse:
            return AIResponse(
                content=import_error_json,
                model="mock-nemotron",
                provider="mock",
                duration_ms=5.0,
            )

    fastapi_app = getattr(async_client._transport, "app", app)
    fastapi_app.dependency_overrides[get_ai_provider_dep] = lambda: (
        ImportErrorMockProvider()
    )

    try:
        reg_resp = await async_client.post(
            f"/api/v1/investigations/{inv_id}/regression-test"
        )
        assert reg_resp.status_code == 200
        data = reg_resp.json()
        assert data["verification_status"] == "EXECUTION_ERROR"
        assert data["verification"]["failure_classification"] == "TEST_EXECUTION_ERROR"

        # Investigation must NOT transition to VERIFYING
        inv_check = await async_client.get(f"/api/v1/investigations/{inv_id}")
        assert inv_check.json()["status"] == "INVESTIGATING"
    finally:
        fastapi_app.dependency_overrides.pop(get_ai_provider_dep, None)


@pytest.mark.asyncio
async def test_regression_test_security_rejection(async_client: AsyncClient) -> None:
    """When the AI produces a test with dangerous AST operations, it is rejected before execution."""
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Security test",
            "bug_description": "Testing dangerous AST rejection.",
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
    await async_client.post(f"/api/v1/investigations/{inv_id}/investigate")

    dangerous_json = json.dumps(
        {
            "test_path": "tests/test_regression.py",
            "framework": "pytest",
            "language": "python",
            "description": "Malicious test attempting subprocess execution",
            "test_content": "import subprocess\n\ndef test_hack():\n    subprocess.run(['ls'])\n",
            "target_symbol": "divide",
            "target_file": "src/calculator.py",
            "expected_failure_reason": "Attack attempt",
        }
    )

    class MaliciousMockProvider(AIProvider):
        @property
        def provider_name(self) -> str:
            return "mock"

        async def generate(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            temperature: float = 0.2,
            max_tokens: int = 2048,
        ) -> AIResponse:
            return AIResponse(
                content=dangerous_json,
                model="mock-nemotron",
                provider="mock",
                duration_ms=5.0,
            )

    fastapi_app = getattr(async_client._transport, "app", app)
    fastapi_app.dependency_overrides[get_ai_provider_dep] = lambda: (
        MaliciousMockProvider()
    )

    try:
        reg_resp = await async_client.post(
            f"/api/v1/investigations/{inv_id}/regression-test"
        )
        assert reg_resp.status_code == 400
        err = reg_resp.json()["error"]
        assert err["code"] == "REGRESSION_SECURITY_VIOLATION"
    finally:
        fastapi_app.dependency_overrides.pop(get_ai_provider_dep, None)


@pytest.mark.asyncio
async def test_regression_test_precondition_failures(async_client: AsyncClient) -> None:
    """Preconditions: cannot generate regression test without REPRODUCED state and hypothesis."""
    # 1. Non-reproduced investigation
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Passing test repo",
            "bug_description": "Everything works.",
        },
    )
    inv_id = inv_resp.json()["id"]

    passing_bytes = PASSING_REPO_ZIP.read_bytes()
    await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={"file": ("passing_python_repo.zip", passing_bytes, "application/zip")},
    )
    await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )

    reg_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/regression-test"
    )
    assert reg_resp.status_code == 400
    assert reg_resp.json()["error"]["code"] == "REGRESSION_PRECONDITION_FAILED"

    # 2. Get regression test when none exists yields 404
    get_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/regression-test"
    )
    assert get_resp.status_code == 404
    assert get_resp.json()["error"]["code"] == "REGRESSION_TEST_NOT_FOUND"


@pytest.mark.asyncio
async def test_regression_test_timeout_is_not_proven(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the test execution times out, verification status is TIMEOUT and not REGRESSION_PROVEN."""
    from sandbox.runner.runner import SandboxResult

    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Timeout test",
            "bug_description": "Testing timeout handling.",
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
    await async_client.post(f"/api/v1/investigations/{inv_id}/investigate")

    def mock_timed_out_execute(*args, **kwargs) -> SandboxResult:
        return SandboxResult(
            exit_code=-1,
            stdout="",
            stderr="Execution timed out after 30 seconds",
            duration_ms=30000.0,
            timed_out=True,
        )

    import app.domain.investigations.regression_service as reg_mod

    monkeypatch.setattr(reg_mod, "execute_command", mock_timed_out_execute)

    reg_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/regression-test"
    )
    assert reg_resp.status_code == 200
    data = reg_resp.json()
    assert data["verification_status"] == "TIMEOUT"
    assert data["verification"]["timed_out"] is True
    assert data["verification"]["failure_classification"] == "TIMEOUT"

    # Investigation must NOT transition to VERIFYING (remains INVESTIGATING)
    inv_check = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert inv_check.json()["status"] == "INVESTIGATING"
