"""Integration tests for Phase 2: Repository Ingestion & Failure Reproduction."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from httpx import AsyncClient

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
BROKEN_REPO_ZIP = FIXTURES_DIR / "broken_python_repo.zip"
PASSING_REPO_ZIP = FIXTURES_DIR / "passing_python_repo.zip"
MALICIOUS_TRAVERSAL_ZIP = FIXTURES_DIR / "malicious_traversal.zip"


@pytest.fixture(autouse=True)
def ensure_fixtures_exist() -> None:
    """Ensure fixture archives are created before tests execute."""
    if (
        not BROKEN_REPO_ZIP.exists()
        or not PASSING_REPO_ZIP.exists()
        or not MALICIOUS_TRAVERSAL_ZIP.exists()
    ):
        from tests.fixtures.generate_fixtures import (
            create_broken_repo_zip,
            create_malicious_traversal_zip,
            create_passing_repo_zip,
        )

        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        create_broken_repo_zip()
        create_passing_repo_zip()
        create_malicious_traversal_zip()


@pytest.mark.asyncio
async def test_repository_ingestion_and_failing_reproduction(
    async_client: AsyncClient,
) -> None:
    """End-to-end happy path:

    Upload broken repo -> verify state INGESTING -> reproduce failure ->
    verify state REPRODUCING & verdict REPRODUCED -> retrieve evidence via API.
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
    assert create_resp.json()["status"] == "CREATED"

    # 2. Upload broken repository ZIP
    broken_bytes = BROKEN_REPO_ZIP.read_bytes()
    upload_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={"file": ("broken_python_repo.zip", broken_bytes, "application/zip")},
    )
    assert upload_resp.status_code == 201
    repo_data = upload_resp.json()
    assert repo_data["name"] == "broken_python_repo.zip"
    assert repo_data["archive_size_bytes"] == len(broken_bytes)
    assert len(repo_data["archive_sha256"]) == 64
    assert repo_data["status"] == "READY"

    # 3. Verify Investigation transitioned: CREATED -> INGESTING
    get_inv_resp = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_inv_resp.status_code == 200
    assert get_inv_resp.json()["status"] == "INGESTING"

    # 4. Retrieve repository metadata
    get_repo_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/repository"
    )
    assert get_repo_resp.status_code == 200
    assert get_repo_resp.json()["id"] == repo_data["id"]
    assert get_repo_resp.json()["archive_sha256"] == repo_data["archive_sha256"]

    # 5. Execute failure reproduction command
    reproduce_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert reproduce_resp.status_code == 200
    run_data = reproduce_resp.json()
    assert run_data["status"] == "REPRODUCED"
    assert run_data["exit_code"] is not None and run_data["exit_code"] > 0
    assert run_data["command"] == "pytest tests/test_bug.py"
    assert "FAILED tests/test_bug.py::test_divide_bug" in run_data["stdout"]
    assert run_data["duration_ms"] is not None and run_data["duration_ms"] > 0
    assert run_data["timed_out"] is False

    # 6. Verify Investigation remains in REPRODUCING status (stops at REPRODUCING in Phase 2)
    get_inv_after = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_inv_after.json()["status"] == "REPRODUCING"

    # 7. Retrieve reproduction result via GET endpoint
    get_run_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/reproduction"
    )
    assert get_run_resp.status_code == 200
    assert get_run_resp.json()["id"] == run_data["id"]
    assert get_run_resp.json()["status"] == "REPRODUCED"
    assert get_run_resp.json()["exit_code"] == run_data["exit_code"]

    # 8. Test Idempotency: repeated reproduce call returns existing run
    idempotent_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert idempotent_resp.status_code == 200
    assert idempotent_resp.json()["id"] == run_data["id"]

    # 9. Verify event timeline includes Phase 2 audit events
    events_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/events")
    assert events_resp.status_code == 200
    event_types = [e["event_type"] for e in events_resp.json()["items"]]
    assert "INVESTIGATION_CREATED" in event_types
    assert "REPOSITORY_INGESTED" in event_types
    assert "REPRODUCTION_STARTED" in event_types
    assert "REPRODUCTION_EVIDENCE_RECORDED" in event_types


@pytest.mark.asyncio
async def test_reproduction_passing_verdict(async_client: AsyncClient) -> None:
    """When the reproduction test passes, verdict is NOT_REPRODUCED."""
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Passing test test",
            "bug_description": "Everything works.",
        },
    )
    inv_id = inv_resp.json()["id"]

    passing_bytes = PASSING_REPO_ZIP.read_bytes()
    await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={"file": ("passing_python_repo.zip", passing_bytes, "application/zip")},
    )

    reproduce_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert reproduce_resp.status_code == 200
    run_data = reproduce_resp.json()
    assert run_data["status"] == "NOT_REPRODUCED"
    assert run_data["exit_code"] == 0
    assert "1 passed" in run_data["stdout"]


@pytest.mark.asyncio
async def test_reject_malicious_traversal_archive(async_client: AsyncClient) -> None:
    """Path traversal in ZIP archives is rejected with 400 INVALID_ARCHIVE."""
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Attack attempt",
            "bug_description": "Zip slip attack.",
        },
    )
    inv_id = inv_resp.json()["id"]

    malicious_bytes = MALICIOUS_TRAVERSAL_ZIP.read_bytes()
    upload_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={"file": ("malicious_traversal.zip", malicious_bytes, "application/zip")},
    )
    assert upload_resp.status_code == 400
    error_payload = upload_resp.json()
    assert error_payload["error"]["code"] == "INVALID_ARCHIVE"
    assert "traversal" in error_payload["error"]["message"].lower()

    # Investigation status must remain CREATED
    inv_get = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert inv_get.json()["status"] == "CREATED"


@pytest.mark.asyncio
async def test_reject_invalid_corrupted_archive(async_client: AsyncClient) -> None:
    """Non-ZIP or corrupted payloads are rejected with 400 INVALID_ARCHIVE."""
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Corrupt upload",
            "bug_description": "Test bad bytes.",
        },
    )
    inv_id = inv_resp.json()["id"]

    upload_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={"file": ("corrupt.zip", b"not-a-valid-zip-file", "application/zip")},
    )
    assert upload_resp.status_code == 400
    assert upload_resp.json()["error"]["code"] == "INVALID_ARCHIVE"


@pytest.mark.asyncio
async def test_reject_policy_blocked_reproduction_commands(
    async_client: AsyncClient,
) -> None:
    """Dangerous or shell-manipulation commands are blocked before execution."""
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Policy test",
            "bug_description": "Test command rejection.",
        },
    )
    inv_id = inv_resp.json()["id"]
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

    blocked_commands = [
        "rm -rf /",
        "bash -c 'pytest'",
        "pytest; echo owned",
        "pytest && cat /etc/passwd",
        "python -c 'import os; os.system(\"ls\")'",
        "pytest | tee out.txt",
    ]

    for cmd in blocked_commands:
        resp = await async_client.post(
            f"/api/v1/investigations/{inv_id}/reproduce",
            json={"command": cmd},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] in {
            "INVALID_REPRODUCTION_COMMAND",
            "EXECUTION_POLICY_BLOCKED",
        }


@pytest.mark.asyncio
async def test_reproduction_without_repository_fails(async_client: AsyncClient) -> None:
    """Attempting reproduction before uploading an archive returns 404 REPOSITORY_NOT_FOUND."""
    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "No repo",
            "bug_description": "Missing repository.",
        },
    )
    inv_id = inv_resp.json()["id"]

    resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "REPOSITORY_NOT_FOUND"


@pytest.mark.asyncio
async def test_reproduction_non_existent_investigation(
    async_client: AsyncClient,
) -> None:
    """Operations on non-existent investigations return 404 INVESTIGATION_NOT_FOUND."""
    random_id = str(uuid4())

    repo_get = await async_client.get(f"/api/v1/investigations/{random_id}/repository")
    assert repo_get.status_code == 404
    assert repo_get.json()["error"]["code"] == "INVESTIGATION_NOT_FOUND"

    run_get = await async_client.get(f"/api/v1/investigations/{random_id}/reproduction")
    assert run_get.status_code == 404
    assert run_get.json()["error"]["code"] == "INVESTIGATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_reproduction_timeout_verdict(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When execution exceeds timeout, verdict is TIMEOUT and timed_out is True."""
    from sandbox.runner.runner import SandboxResult

    def mock_timeout_execute(*args, **kwargs) -> SandboxResult:
        return SandboxResult(
            exit_code=124,
            stdout="",
            stderr="Execution timed out after 30 seconds",
            duration_ms=30005.0,
            timed_out=True,
            command="pytest",
        )

    monkeypatch.setattr(
        "app.domain.repositories.reproduction_service.execute_command",
        mock_timeout_execute,
    )

    inv_resp = await async_client.post(
        "/api/v1/investigations",
        json={
            "repository_id": str(uuid4()),
            "title": "Timeout test",
            "bug_description": "Hangs indefinitely.",
        },
    )
    inv_id = inv_resp.json()["id"]

    broken_bytes = BROKEN_REPO_ZIP.read_bytes()
    await async_client.post(
        f"/api/v1/investigations/{inv_id}/repository",
        files={"file": ("broken_python_repo.zip", broken_bytes, "application/zip")},
    )

    reproduce_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/reproduce",
        json={"command": "pytest tests/test_bug.py"},
    )
    assert reproduce_resp.status_code == 200
    run_data = reproduce_resp.json()
    assert run_data["status"] == "TIMEOUT"
    assert run_data["timed_out"] is True
    assert run_data["exit_code"] == 124
