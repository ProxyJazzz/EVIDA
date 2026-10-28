"""Unit tests for Phase 6 PatchVerificationService."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from app.core.config import Settings
from app.domain.investigations.models import (
    EventType,
    Investigation,
    InvestigationEvent,
    InvestigationHypothesisRecord,
    InvestigationRegressionTestRecord,
    InvestigationStatus,
    RegressionVerificationStatus,
)
from app.domain.investigations.repository import InMemoryInvestigationRepository
from app.domain.investigations.service import InvestigationService
from app.domain.investigations.state_machine import LifecycleException
from app.domain.patches.models import PatchCandidateRecord, PatchCandidateStatus
from app.domain.repositories.models import (
    Repository,
    RepositoryStatus,
    ReproductionRun,
    ReproductionStatus,
)
from app.domain.verification.models import (
    PatchVerificationStatus,
    PatchVerificationVerdict,
    VerificationFailureClassification,
)
from app.domain.verification.patch_verification_service import PatchVerificationService

from sandbox.runner.runner import SandboxResult

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
BROKEN_REPO_ZIP = FIXTURES_DIR / "broken_python_repo.zip"


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        PATCH_APPLICATION_TIMEOUT_SECONDS=5.0,
        REGRESSION_VERIFICATION_TIMEOUT_SECONDS=5.0,
        BASELINE_VERIFICATION_TIMEOUT_SECONDS=5.0,
    )


@pytest.fixture
def in_memory_repo() -> InMemoryInvestigationRepository:
    return InMemoryInvestigationRepository()


@pytest.fixture
def investigation_service(
    in_memory_repo: InMemoryInvestigationRepository,
) -> InvestigationService:
    return InvestigationService(in_memory_repo)


@pytest.fixture
def verification_service(
    in_memory_repo: InMemoryInvestigationRepository,
    investigation_service: InvestigationService,
    test_settings: Settings,
) -> PatchVerificationService:
    return PatchVerificationService(
        in_memory_repo, investigation_service, test_settings
    )


async def setup_ready_investigation(
    repo: InMemoryInvestigationRepository,
    *,
    status: InvestigationStatus = InvestigationStatus.VERIFYING,
    repro_status: ReproductionStatus = ReproductionStatus.REPRODUCED,
    regression_status: RegressionVerificationStatus = RegressionVerificationStatus.REGRESSION_PROVEN,
    patch_status: PatchCandidateStatus = PatchCandidateStatus.VALIDATED,
) -> tuple[Investigation, PatchCandidateRecord, InvestigationRegressionTestRecord]:
    inv_id = uuid4()
    repo_id = uuid4()
    archive_bytes = BROKEN_REPO_ZIP.read_bytes()
    archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()

    # Investigation
    inv = Investigation(
        id=inv_id,
        user_id="user_123",
        project_id=uuid4(),
        repository_id=repo_id,
        title="Test Investigation",
        bug_description="divide multiplies instead of dividing",
        status=status,
    )
    event = InvestigationEvent(
        id=uuid4(),
        investigation_id=inv_id,
        event_type=EventType.INVESTIGATION_CREATED,
        from_status=None,
        to_status=status,
    )
    await repo.create(inv, event)

    # Repository
    storage_path = f"test/{inv_id}.zip"
    repository = Repository(
        id=repo_id,
        investigation_id=inv_id,
        name="broken_python_repo.zip",
        storage_path=storage_path,
        archive_size_bytes=len(archive_bytes),
        archive_sha256=archive_sha256,
        status=RepositoryStatus.READY,
    )
    await repo.save_repository(repository)
    await repo.save_archive_bytes(storage_path, archive_bytes)

    # Reproduction
    repro = ReproductionRun(
        id=uuid4(),
        investigation_id=inv_id,
        repository_id=repo_id,
        command="pytest tests/test_bug.py",
        status=repro_status,
        exit_code=1 if repro_status == ReproductionStatus.REPRODUCED else 0,
        stdout="FAILED assert 20 == 5",
        stderr="",
        duration_ms=100,
        timed_out=False,
    )
    await repo.save_reproduction_run(repro)

    # Hypothesis
    hypo = InvestigationHypothesisRecord(
        id=uuid4(),
        investigation_id=inv_id,
        reproduction_run_id=repro.id,
        hypothesis="Divide function multiplies operands instead of dividing",
        confidence=0.99,
        model="nvidia/Nemotron-3_5-Lightning",
        provider="nebius",
        root_cause={
            "file": "src/calculator.py",
            "symbol": "divide",
            "line": 2,
            "description": "The divide function multiplies instead of dividing.",
        },
        affected_files=["src/calculator.py"],
        evidence=["Returns 20 instead of 5"],
        recommended_next_action="Generate regression test",
    )
    await repo.save_hypothesis(hypo)

    # Regression test
    reg = InvestigationRegressionTestRecord(
        id=uuid4(),
        investigation_id=inv_id,
        hypothesis_id=hypo.id,
        test_path="tests/test_regression.py",
        framework="pytest",
        language="python",
        description="Verify divide returns 5",
        test_content="from src.calculator import divide\n\ndef test_regression():\n    assert divide(10, 2) == 5\n",
        target_symbol="divide",
        target_file="src/calculator.py",
        expected_failure_reason="Returns 20 instead of 5",
        verification_status=regression_status,
    )
    saved_reg = await repo.save_regression_test(reg)

    # Patch candidate
    patch_rec = PatchCandidateRecord(
        id=uuid4(),
        investigation_id=inv_id,
        hypothesis_id=hypo.id,
        regression_test_id=saved_reg.id,
        status=patch_status,
        description="Fix divide implementation",
        patch_format="unified_diff",
        patch_content=(
            "--- a/src/calculator.py\n"
            "+++ b/src/calculator.py\n"
            "@@ -1,3 +1,3 @@\n"
            " def divide(a: int, b: int) -> int:\n"
            "     # Bug: multiplication instead of division\n"
            "-    return a * b\n"
            "+    return a // b\n"
        ),
        changed_files=["src/calculator.py"],
        change_summary=[{"file": "src/calculator.py", "reason": "Change * to /"}],
        reasoning="Multiplication bug",
        prompt_version="evida-patch-generation-v1",
    )
    saved_patch = await repo.save_patch_candidate(patch_rec)

    return inv, saved_patch, saved_reg


@pytest.mark.asyncio
async def test_precondition_not_in_verifying_status(
    in_memory_repo: InMemoryInvestigationRepository,
    verification_service: PatchVerificationService,
):
    inv, _, _ = await setup_ready_investigation(
        in_memory_repo, status=InvestigationStatus.INVESTIGATING
    )
    with pytest.raises(LifecycleException) as exc_info:
        await verification_service.verify_patch_candidate(inv.id)
    assert exc_info.value.code == "INVESTIGATION_PRECONDITION_FAILED"
    assert "requires 'VERIFYING'" in exc_info.value.message


@pytest.mark.asyncio
async def test_precondition_regression_not_proven(
    in_memory_repo: InMemoryInvestigationRepository,
    verification_service: PatchVerificationService,
):
    inv, _, _ = await setup_ready_investigation(
        in_memory_repo, regression_status=RegressionVerificationStatus.TEST_REJECTED
    )
    with pytest.raises(LifecycleException) as exc_info:
        await verification_service.verify_patch_candidate(inv.id)
    assert exc_info.value.code == "INVESTIGATION_PRECONDITION_FAILED"
    assert "proven regression test" in exc_info.value.message


@pytest.mark.asyncio
async def test_precondition_patch_not_validated(
    in_memory_repo: InMemoryInvestigationRepository,
    verification_service: PatchVerificationService,
):
    inv, _, _ = await setup_ready_investigation(
        in_memory_repo, patch_status=PatchCandidateStatus.REJECTED
    )
    with pytest.raises(LifecycleException) as exc_info:
        await verification_service.verify_patch_candidate(inv.id)
    assert exc_info.value.code == "INVESTIGATION_PRECONDITION_FAILED"
    assert "validated candidate patch" in exc_info.value.message


@pytest.mark.asyncio
async def test_successful_double_validation(
    in_memory_repo: InMemoryInvestigationRepository,
    verification_service: PatchVerificationService,
):
    inv, _patch_cand, _reg_test = await setup_ready_investigation(in_memory_repo)

    result = await verification_service.verify_patch_candidate(inv.id)

    assert result.verdict == PatchVerificationVerdict.VERIFIED
    assert result.status == PatchVerificationStatus.VERIFIED
    assert result.failure_classification is None
    assert result.patch_application.status == "APPLIED"
    assert result.regression_execution.status == "PASSED"
    assert result.baseline_execution.status == "PASSED"
    assert result.source_integrity_verified is True

    # Confirm lifecycle transitioned to COMPLETED
    updated_inv = await in_memory_repo.get_by_id(inv.id)
    assert updated_inv is not None
    assert updated_inv.status == InvestigationStatus.COMPLETED


@pytest.mark.asyncio
async def test_idempotent_verification(
    in_memory_repo: InMemoryInvestigationRepository,
    verification_service: PatchVerificationService,
):
    inv, _, _ = await setup_ready_investigation(in_memory_repo)

    first_res = await verification_service.verify_patch_candidate(inv.id)
    second_res = await verification_service.verify_patch_candidate(inv.id)

    assert first_res.id == second_res.id
    assert second_res.verdict == PatchVerificationVerdict.VERIFIED


@pytest.mark.asyncio
async def test_regression_still_failing(
    in_memory_repo: InMemoryInvestigationRepository,
    verification_service: PatchVerificationService,
):
    inv, patch_cand, _ = await setup_ready_investigation(in_memory_repo)
    # Give it a useless patch that doesn't fix divide
    patch_cand.patch_content = (
        "--- a/src/calculator.py\n"
        "+++ b/src/calculator.py\n"
        "@@ -1,3 +1,3 @@\n"
        " def divide(a: int, b: int) -> int:\n"
        "     # Bug: multiplication instead of division\n"
        "-    return a * b\n"
        "+    return a * b + 0\n"
    )
    await in_memory_repo.save_patch_candidate(patch_cand)

    result = await verification_service.verify_patch_candidate(inv.id)

    assert result.verdict == PatchVerificationVerdict.UNVERIFIED
    assert (
        result.failure_classification
        == VerificationFailureClassification.REGRESSION_STILL_FAILING
    )
    assert result.regression_execution.status == "FAILED"
    assert result.baseline_execution.status == "SKIPPED"

    # Confirm investigation status remains VERIFYING (not failed, not completed)
    updated_inv = await in_memory_repo.get_by_id(inv.id)
    assert updated_inv is not None
    assert updated_inv.status == InvestigationStatus.VERIFYING


@pytest.mark.asyncio
async def test_baseline_test_failure(
    in_memory_repo: InMemoryInvestigationRepository,
    verification_service: PatchVerificationService,
):
    inv, _patch_cand, _ = await setup_ready_investigation(in_memory_repo)

    # Mock execute_command in patch_verification_service so regression passes, but baseline suite fails
    with patch(
        "app.domain.verification.patch_verification_service.execute_command"
    ) as mock_exec:
        # Call 1: pytest tests/test_regression.py -> exit 0 (passes)
        # Call 2: pytest (baseline) -> exit 1 (fails)
        mock_exec.side_effect = [
            SandboxResult(exit_code=0, stdout="1 passed", stderr="", duration_ms=20.0),
            SandboxResult(
                exit_code=1,
                stdout="1 failed",
                stderr="AssertionError",
                duration_ms=30.0,
            ),
        ]

        result = await verification_service.verify_patch_candidate(inv.id)

        assert result.verdict == PatchVerificationVerdict.UNVERIFIED
        assert (
            result.failure_classification
            == VerificationFailureClassification.BASELINE_TEST_FAILURE
        )
        assert result.regression_execution.status == "PASSED"
        assert result.baseline_execution.status == "FAILED"

        # Lifecycle remains VERIFYING
        updated_inv = await in_memory_repo.get_by_id(inv.id)
        assert updated_inv is not None
        assert updated_inv.status == InvestigationStatus.VERIFYING


@pytest.mark.asyncio
async def test_tenant_authorization_precondition(
    in_memory_repo: InMemoryInvestigationRepository,
    verification_service: PatchVerificationService,
):
    inv, _, _ = await setup_ready_investigation(in_memory_repo)
    # Attempt verification by different user
    with pytest.raises(LifecycleException) as exc_info:
        await verification_service.verify_patch_candidate(
            inv.id, user_id="other_user_999"
        )
    assert exc_info.value.code == "INVESTIGATION_PRECONDITION_FAILED"
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_regression_execution_error_classification(
    in_memory_repo: InMemoryInvestigationRepository,
    verification_service: PatchVerificationService,
):
    inv, _, _ = await setup_ready_investigation(in_memory_repo)
    with patch(
        "app.domain.verification.patch_verification_service.execute_command"
    ) as mock_exec:
        # Exit code 2 = pytest collection / syntax crash
        mock_exec.return_value = SandboxResult(
            exit_code=2,
            stdout="",
            stderr="ERROR collecting tests/test_regression.py",
            duration_ms=25.0,
        )

        result = await verification_service.verify_patch_candidate(inv.id)
        assert result.verdict == PatchVerificationVerdict.UNVERIFIED
        assert (
            result.failure_classification
            == VerificationFailureClassification.REGRESSION_EXECUTION_ERROR
        )
        assert result.regression_execution.status == "FAILED"


@pytest.mark.asyncio
async def test_source_integrity_violation_detection(
    in_memory_repo: InMemoryInvestigationRepository,
    verification_service: PatchVerificationService,
):
    inv, _, _ = await setup_ready_investigation(in_memory_repo)
    repo_meta = await in_memory_repo.get_repository_by_investigation_id(inv.id)
    assert repo_meta is not None and repo_meta.storage_path is not None

    # We simulate tampering with stored repository archive right before step 6
    original_get_archive = in_memory_repo.get_archive_bytes

    call_count = 0

    async def tampered_get_archive(path: str) -> bytes | None:
        nonlocal call_count
        call_count += 1
        res = await original_get_archive(path)
        if call_count > 1 and res is not None:
            # Tamper the post-check archive bytes
            return res + b"CORRUPTED_MUTATION"
        return res

    with patch.object(
        in_memory_repo, "get_archive_bytes", side_effect=tampered_get_archive
    ):
        result = await verification_service.verify_patch_candidate(inv.id)

        assert result.verdict == PatchVerificationVerdict.UNVERIFIED
        assert (
            result.failure_classification
            == VerificationFailureClassification.SOURCE_INTEGRITY_VIOLATION
        )
        assert result.source_integrity_verified is False


@pytest.mark.asyncio
async def test_patch_application_unexpected_workspace_change(
    in_memory_repo: InMemoryInvestigationRepository,
    verification_service: PatchVerificationService,
):
    inv, patch_cand, _ = await setup_ready_investigation(in_memory_repo)
    # Patch modifies a test file, which violates test immutability
    patch_cand.patch_content = (
        "--- a/tests/test_bug.py\n"
        "+++ b/tests/test_bug.py\n"
        "@@ -6,1 +6,1 @@\n"
        "-    assert divide(10, 2) == 5\n"
        "+    assert True\n"
    )
    patch_cand.changed_files = ["tests/test_bug.py"]
    await in_memory_repo.save_patch_candidate(patch_cand)

    result = await verification_service.verify_patch_candidate(inv.id)

    assert result.verdict == PatchVerificationVerdict.UNVERIFIED
    assert (
        result.failure_classification
        == VerificationFailureClassification.UNEXPECTED_WORKSPACE_CHANGE
    )
    assert result.patch_application.status == "FAILED"
