"""Integration tests for Phase 6: Deterministic Patch Verification & Double Validation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from app.domain.verification.models import (
    VerificationFailureClassification,
)
from httpx import AsyncClient

from sandbox.runner.runner import SandboxResult

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
BROKEN_REPO_ZIP = FIXTURES_DIR / "broken_python_repo.zip"


@pytest.fixture(autouse=True)
def ensure_fixtures_exist() -> None:
    """Ensure fixture archives are created before tests execute."""
    if not BROKEN_REPO_ZIP.exists():
        from tests.fixtures.generate_fixtures import create_broken_repo_zip

        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        create_broken_repo_zip()


async def setup_validated_patch_investigation(
    async_client: AsyncClient,
) -> tuple[str, bytes]:
    """Helper creating an investigation with validated candidate patch in VERIFYING state."""
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

    # 3. Reproduce failure (exit code 1)
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

    # 6. Generate and validate candidate patch
    patch_resp = await async_client.post(f"/api/v1/investigations/{inv_id}/patch")
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "VALIDATED"
    assert patch_resp.json()["verification_status"] == "NOT_VERIFIED"

    # Verify investigation status is VERIFYING
    get_inv = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_inv.json()["status"] == "VERIFYING"

    return inv_id, broken_bytes


@pytest.mark.asyncio
async def test_patch_verification_happy_path(async_client: AsyncClient) -> None:
    """Full end-to-end double validation success path:

    broken repo -> reproduced -> hypothesis -> regression proven -> patch validated
    -> POST /verify-patch:
        - applies candidate patch in fresh ephemeral workspace
        - executes proven regression test (PASS)
        - executes baseline test suite (PASS)
        - verifies repository SHA-256 before == after
        - assigns VERIFIED verdict
        - transitions lifecycle VERIFYING -> COMPLETED.
    """
    inv_id, original_bytes = await setup_validated_patch_investigation(async_client)
    original_sha256 = hashlib.sha256(original_bytes).hexdigest()

    # 1. Execute Double Validation
    verify_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/verify-patch"
    )
    assert verify_resp.status_code == 200
    data = verify_resp.json()

    assert data["investigation_id"] == inv_id
    assert data["status"] == "VERIFIED"
    assert data["verdict"] == "VERIFIED"
    assert data["failure_classification"] is None

    # Patch application evidence
    assert data["patch_application"]["status"] == "APPLIED"
    assert data["patch_application"]["exit_code"] == 0
    assert "src/calculator.py" in data["patch_application"]["modified_files"]

    # Regression test evidence
    assert data["regression_execution"]["status"] == "PASSED"
    assert data["regression_execution"]["exit_code"] == 0

    # Baseline suite evidence
    assert data["baseline_execution"]["status"] == "PASSED"
    assert data["baseline_execution"]["exit_code"] == 0

    # Cryptographic source integrity evidence
    assert data["repository_sha256"] == original_sha256
    assert data["source_integrity_verified"] is True

    # Workspace file manifest captured
    assert "src/calculator.py" in data["workspace_file_manifest"]

    # 2. Lifecycle transition: VERIFYING -> COMPLETED
    inv_resp = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert inv_resp.status_code == 200
    assert inv_resp.json()["status"] == "COMPLETED"

    # 3. Candidate patch record must now reflect VERIFIED
    patch_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/patch")
    assert patch_resp.status_code == 200
    assert patch_resp.json()["verification_status"] == "VERIFIED"

    # 4. Source archive in repository endpoint must remain identical
    repo_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/repository")
    assert repo_resp.status_code == 200
    assert repo_resp.json()["archive_sha256"] == original_sha256

    # 5. GET /verification returns the latest run
    latest_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/verification"
    )
    assert latest_resp.status_code == 200
    assert latest_resp.json()["id"] == data["id"]
    assert latest_resp.json()["verdict"] == "VERIFIED"

    # 6. GET /verifications returns history list
    list_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/verifications")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert len(runs) >= 1
    assert runs[0]["id"] == data["id"]

    # 7. Idempotency: repeated call returns existing verified record
    repeat_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/verify-patch"
    )
    assert repeat_resp.status_code == 200
    assert repeat_resp.json()["id"] == data["id"]

    # 8. Audit event verification
    events_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/events")
    assert events_resp.status_code == 200
    types = [e["event_type"] for e in events_resp.json()["items"]]
    assert "PATCH_VERIFICATION_STARTED" in types
    assert "PATCH_APPLICATION_STARTED" in types
    assert "PATCH_APPLICATION_COMPLETED" in types
    assert "REGRESSION_VERIFICATION_PASSED" in types
    assert "BASELINE_VERIFICATION_STARTED" in types
    assert "BASELINE_VERIFICATION_PASSED" in types
    assert "SOURCE_INTEGRITY_CHECKED" in types
    assert "PATCH_VERIFIED" in types


@pytest.mark.asyncio
async def test_verification_negative_regression_still_failing(
    async_client: AsyncClient,
) -> None:
    """When the candidate patch does not fix the regression, verdict must be UNVERIFIED.

    Failure classification: REGRESSION_STILL_FAILING.
    Lifecycle must remain in VERIFYING (not failed or completed).
    """
    inv_id, _ = await setup_validated_patch_investigation(async_client)

    # Mock execute_command in patch_verification_service to return exit code 1 on regression test
    with patch(
        "app.domain.verification.patch_verification_service.execute_command"
    ) as mock_exec:
        # Regression execution fails
        mock_exec.return_value = SandboxResult(
            exit_code=1,
            stdout="FAILED tests/test_regression.py::test_divide_regression - AssertionError: assert 20 == 5",
            stderr="",
            duration_ms=45.0,
        )

        resp = await async_client.post(f"/api/v1/investigations/{inv_id}/verify-patch")
        assert resp.status_code == 200
        data = resp.json()

        assert data["verdict"] == "UNVERIFIED"
        assert data["status"] == "UNVERIFIED"
        assert (
            data["failure_classification"]
            == VerificationFailureClassification.REGRESSION_STILL_FAILING.value
        )
        assert data["regression_execution"]["status"] == "FAILED"
        assert data["baseline_execution"]["status"] == "SKIPPED"

        # Lifecycle remains VERIFYING for further review
        inv_check = await async_client.get(f"/api/v1/investigations/{inv_id}")
        assert inv_check.json()["status"] == "VERIFYING"


@pytest.mark.asyncio
async def test_verification_negative_baseline_suite_failure(
    async_client: AsyncClient,
) -> None:
    """When regression test passes but baseline suite fails, verdict must be UNVERIFIED.

    Failure classification: BASELINE_TEST_FAILURE.
    Demonstrates double validation protecting existing functionality.
    """
    inv_id, _ = await setup_validated_patch_investigation(async_client)

    with patch(
        "app.domain.verification.patch_verification_service.execute_command"
    ) as mock_exec:
        # Call 1: regression passes
        # Call 2: baseline suite fails (e.g. regression broke unrelated test)
        mock_exec.side_effect = [
            SandboxResult(
                exit_code=0,
                stdout="1 passed in 0.05s",
                stderr="",
                duration_ms=50.0,
            ),
            SandboxResult(
                exit_code=1,
                stdout="FAILED tests/test_other.py::test_existing_feature - AssertionError",
                stderr="",
                duration_ms=80.0,
            ),
        ]

        resp = await async_client.post(f"/api/v1/investigations/{inv_id}/verify-patch")
        assert resp.status_code == 200
        data = resp.json()

        assert data["verdict"] == "UNVERIFIED"
        assert (
            data["failure_classification"]
            == VerificationFailureClassification.BASELINE_TEST_FAILURE.value
        )
        assert data["regression_execution"]["status"] == "PASSED"
        assert data["baseline_execution"]["status"] == "FAILED"

        # Lifecycle remains VERIFYING
        inv_check = await async_client.get(f"/api/v1/investigations/{inv_id}")
        assert inv_check.json()["status"] == "VERIFYING"


@pytest.mark.asyncio
async def test_verification_negative_regression_timeout(
    async_client: AsyncClient,
) -> None:
    """When regression test times out, verdict must be UNVERIFIED with REGRESSION_TIMEOUT."""
    inv_id, _ = await setup_validated_patch_investigation(async_client)

    with patch(
        "app.domain.verification.patch_verification_service.execute_command"
    ) as mock_exec:
        mock_exec.return_value = SandboxResult(
            exit_code=-1,
            stdout="",
            stderr="Execution timed out after 30.0s",
            duration_ms=30000.0,
            timed_out=True,
        )

        resp = await async_client.post(f"/api/v1/investigations/{inv_id}/verify-patch")
        assert resp.status_code == 200
        data = resp.json()

        assert data["verdict"] == "UNVERIFIED"
        assert (
            data["failure_classification"]
            == VerificationFailureClassification.REGRESSION_TIMEOUT.value
        )
        assert data["regression_execution"]["status"] == "TIMEOUT"


@pytest.mark.asyncio
async def test_verification_precondition_failures(async_client: AsyncClient) -> None:
    """Verification must reject execution with 400 INVESTIGATION_PRECONDITION_FAILED

    if investigation is not in VERIFYING status or required artifacts are missing.
    """
    proj_id = str(uuid4())
    repo_id = str(uuid4())

    # Create investigation in CREATED state
    create_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "project_id": proj_id,
            "repository_id": repo_id,
            "title": "Unprepared investigation",
            "bug_description": "Cannot verify yet.",
        },
    )
    inv_id = create_resp.json()["id"]

    # Verify attempt must fail with 400
    verify_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/verify-patch"
    )
    assert verify_resp.status_code == 400
    body = verify_resp.json()
    assert (
        body.get("code") == "INVESTIGATION_PRECONDITION_FAILED"
        or "INVESTIGATION_PRECONDITION_FAILED" in body.get("error", {}).get("code", "")
    )


@pytest.mark.asyncio
async def test_verification_not_found(async_client: AsyncClient) -> None:
    """Non-existent investigation must return 404."""
    random_id = str(uuid4())
    resp = await async_client.get(f"/api/v1/investigations/{random_id}/verification")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_verification_tenant_isolation(async_client: AsyncClient) -> None:
    """User B cannot access or verify User A's investigation."""
    headers_a = {"Authorization": "Bearer user_a_token_secret"}
    headers_b = {"Authorization": "Bearer user_b_token_secret"}

    # User A creates investigation
    create_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "project_id": str(uuid4()),
            "repository_id": str(uuid4()),
            "title": "Tenant Isolation Test",
            "bug_description": "User A secret bug",
        },
        headers=headers_a,
    )
    assert create_resp.status_code == 201
    inv_id = create_resp.json()["id"]

    # User B tries to verify User A's investigation
    verify_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/verify-patch",
        headers=headers_b,
    )
    assert verify_resp.status_code == 403
    assert "INVESTIGATION_PRECONDITION_FAILED" in str(verify_resp.json())

    # User B tries to read User A's verification
    get_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/verification",
        headers=headers_b,
    )
    assert get_resp.status_code == 403


@pytest.mark.asyncio
async def test_verification_bad_patch_real_execution(async_client: AsyncClient) -> None:
    """Real deterministic execution of a bad candidate patch that fails to fix the bug.

    Does not use mocks for execute_command.
    Expected: UNVERIFIED with REGRESSION_STILL_FAILING.
    """
    inv_id, _ = await setup_validated_patch_investigation(async_client)

    # Invalidate patch with a useless non-fixing patch in repo directly
    from uuid import UUID

    from app.api.dependencies import get_investigation_repository
    from app.core.config import get_settings

    repo = get_investigation_repository(get_settings())
    cand = await repo.get_patch_candidate_by_investigation_id(UUID(inv_id))
    assert cand is not None
    cand.patch_content = (
        "--- a/src/calculator.py\n"
        "+++ b/src/calculator.py\n"
        "@@ -1,3 +1,3 @@\n"
        " def divide(a: int, b: int) -> int:\n"
        "     # Bug: multiplication instead of division\n"
        "-    return a * b\n"
        "+    return a * b + 0\n"
    )
    await repo.save_patch_candidate(cand)

    verify_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/verify-patch"
    )
    assert verify_resp.status_code == 200
    data = verify_resp.json()

    assert data["verdict"] == "UNVERIFIED"
    assert data["status"] == "UNVERIFIED"
    assert data["failure_classification"] == "REGRESSION_STILL_FAILING"
    assert data["regression_execution"]["status"] == "FAILED"
    assert data["baseline_execution"]["status"] == "SKIPPED"


@pytest.mark.asyncio
async def test_verification_baseline_failure_real_execution(
    async_client: AsyncClient,
) -> None:
    """Real deterministic execution of a patch that fixes the regression but breaks baseline tests.

    Expected: UNVERIFIED with BASELINE_TEST_FAILURE.
    """
    import io
    import zipfile
    from uuid import UUID

    from app.api.dependencies import get_investigation_repository
    from app.core.config import get_settings

    # Build repo archive with both bug test and baseline test
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("multi_repo/src/__init__.py", "")
        zf.writestr(
            "multi_repo/src/calculator.py",
            "def divide(a: int, b: int) -> int:\n"
            "    return a * b\n\n"
            "def add(a: int, b: int) -> int:\n"
            "    return a + b\n",
        )
        zf.writestr("multi_repo/tests/__init__.py", "")
        zf.writestr(
            "multi_repo/tests/test_bug.py",
            "import sys\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))\n"
            "from calculator import divide\n\n"
            "def test_divide_bug():\n"
            "    assert divide(10, 2) == 5\n",
        )
        zf.writestr(
            "multi_repo/tests/test_baseline.py",
            "import sys\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))\n"
            "from calculator import add\n\n"
            "def test_add_baseline():\n"
            "    assert add(2, 3) == 5\n",
        )
        zf.writestr(
            "multi_repo/pyproject.toml",
            "[project]\nname = 'multi'\nversion = '0.1.0'\n",
        )
    repo_bytes = buf.getvalue()

    # 1. Create Investigation
    create_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "project_id": str(uuid4()),
            "repository_id": str(uuid4()),
            "title": "Baseline break test",
            "bug_description": "divide returns 20 instead of 5",
        },
    )
    inv_id = create_resp.json()["id"]

    # 2. Upload archive
    upload_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={"file": ("multi_repo.zip", repo_bytes, "application/zip")},
    )
    assert upload_resp.status_code == 201

    # 3. Reproduce failure
    repro_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert repro_resp.status_code == 200

    # 4. Formulate hypothesis
    await async_client.post(f"/api/v1/investigations/{inv_id}/investigate")

    # 5. Regression test
    await async_client.post(f"/api/v1/investigations/{inv_id}/regression-test")

    # 6. Generate patch
    await async_client.post(f"/api/v1/investigations/{inv_id}/patch")

    # 7. Update patch candidate to fix divide but break add
    repo = get_investigation_repository(get_settings())
    cand = await repo.get_patch_candidate_by_investigation_id(UUID(inv_id))
    assert cand is not None
    cand.patch_content = (
        "--- a/src/calculator.py\n"
        "+++ b/src/calculator.py\n"
        "@@ -1,5 +1,5 @@\n"
        " def divide(a: int, b: int) -> int:\n"
        "-    return a * b\n"
        "+    return a // b\n"
        " \n"
        " def add(a: int, b: int) -> int:\n"
        "-    return a + b\n"
        "+    return 0\n"
    )
    await repo.save_patch_candidate(cand)

    # 8. Verify patch: regression test will pass, but baseline test suite will fail!
    verify_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/verify-patch"
    )
    assert verify_resp.status_code == 200
    data = verify_resp.json()

    assert data["verdict"] == "UNVERIFIED"
    assert data["status"] == "UNVERIFIED"
    assert data["failure_classification"] == "BASELINE_TEST_FAILURE"
    assert data["regression_execution"]["status"] == "PASSED"
    assert data["baseline_execution"]["status"] == "FAILED"
    assert "test_add_baseline" in data["baseline_execution"]["stdout"]
