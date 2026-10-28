"""Deterministic Patch Verification & Double Validation Domain Service (Phase 6)

Executes candidate patches inside an isolated ephemeral workspace restored from the original
unpatched repository archive. Enforces double validation:
1. Proven regression test must PASS.
2. Baseline test suite must PASS.
Original source repository archive is verified to remain cryptographically identical.
"""

from __future__ import annotations

import hashlib
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from sandbox.runner.runner import execute_command

from app.core.config import Settings
from app.core.logging import get_logger
from app.domain.investigations.models import (
    EventType,
    InvestigationStatus,
    RegressionVerificationStatus,
)
from app.domain.investigations.repository import InvestigationRepository
from app.domain.investigations.service import InvestigationService
from app.domain.investigations.state_machine import InvestigationNotFoundError, LifecycleException
from app.domain.patches.models import PatchCandidateStatus
from app.domain.repositories.archive_validator import extract_archive_safely
from app.domain.repositories.models import ReproductionStatus
from app.domain.verification.models import (
    PatchApplicationResponse,
    PatchVerificationResponse,
    PatchVerificationRun,
    PatchVerificationStatus,
    PatchVerificationVerdict,
    VerificationFailureClassification,
    VerificationTestResponse,
)
from app.domain.verification.patch_applier import apply_patch_to_workspace

logger = get_logger("evida.verification.service")


class PatchVerificationService:
    """Orchestrates deterministic patch verification and double validation."""

    def __init__(
        self,
        repo: InvestigationRepository,
        investigation_service: InvestigationService,
        settings: Settings,
    ) -> None:
        self.repo = repo
        self.investigation_service = investigation_service
        self.settings = settings

    async def verify_patch_candidate(self, investigation_id: UUID) -> PatchVerificationResponse:
        """Execute deterministic double validation on the latest candidate patch."""
        # 1. Precondition checks
        inv = await self.repo.get_by_id(investigation_id)
        if inv is None:
            raise InvestigationNotFoundError(str(investigation_id))

        # 1. Idempotency Check: if this patch candidate was already verified successfully
        patch_candidate = await self.repo.get_patch_candidate_by_investigation_id(investigation_id)
        if patch_candidate is not None:
            existing_run = await self.repo.get_patch_verification_run_by_investigation_id(
                investigation_id
            )
            if (
                existing_run is not None
                and existing_run.patch_candidate_id == patch_candidate.id
                and existing_run.verdict == PatchVerificationVerdict.VERIFIED
            ):
                logger.info(
                    "Returning existing successful verification run %s for investigation %s",
                    existing_run.id,
                    investigation_id,
                )
                return self._to_response(existing_run)

        # 2. Precondition checks
        if inv.status != InvestigationStatus.VERIFYING:
            raise LifecycleException(
                f"Investigation '{investigation_id}' is in status '{inv.status}', "
                f"but patch verification requires '{InvestigationStatus.VERIFYING}'.",
                code="INVESTIGATION_PRECONDITION_FAILED",
                status_code=400,
            )

        repo_meta = await self.repo.get_repository_by_investigation_id(investigation_id)
        if repo_meta is None or not repo_meta.storage_path:
            raise LifecycleException(
                "No repository archive metadata found for this investigation.",
                code="INVESTIGATION_PRECONDITION_FAILED",
                status_code=400,
            )

        archive_bytes = await self.repo.get_archive_bytes(repo_meta.storage_path)
        if not archive_bytes:
            raise LifecycleException(
                "Stored repository archive payload is missing or empty.",
                code="INVESTIGATION_PRECONDITION_FAILED",
                status_code=400,
            )

        repro_run = await self.repo.get_reproduction_run_by_investigation_id(investigation_id)
        if repro_run is None or repro_run.status != ReproductionStatus.REPRODUCED:
            raise LifecycleException(
                "Reproduction evidence must be verified with status 'REPRODUCED'.",
                code="INVESTIGATION_PRECONDITION_FAILED",
                status_code=400,
            )

        hypothesis = await self.repo.get_hypothesis_by_investigation_id(investigation_id)
        if hypothesis is None:
            raise LifecycleException(
                "A causal hypothesis must exist before patch verification.",
                code="INVESTIGATION_PRECONDITION_FAILED",
                status_code=400,
            )

        regression_test = await self.repo.get_regression_test_by_investigation_id(investigation_id)
        if (
            regression_test is None
            or regression_test.verification_status != RegressionVerificationStatus.REGRESSION_PROVEN
        ):
            raise LifecycleException(
                "A proven regression test ('REGRESSION_PROVEN') is required for patch verification.",
                code="INVESTIGATION_PRECONDITION_FAILED",
                status_code=400,
            )

        if patch_candidate is None or patch_candidate.status != PatchCandidateStatus.VALIDATED:
            raise LifecycleException(
                "A validated candidate patch ('VALIDATED') is required for patch verification.",
                code="INVESTIGATION_PRECONDITION_FAILED",
                status_code=400,
            )

        # 3. Source Integrity Pre-Check
        sha256_before = hashlib.sha256(archive_bytes).hexdigest()
        patch_sha256 = hashlib.sha256(patch_candidate.patch_content.encode("utf-8")).hexdigest()

        # Audit events: start verification and patch application
        await self.investigation_service.record_event(
            investigation_id=investigation_id,
            event_type=EventType.PATCH_VERIFICATION_STARTED,
            from_status=inv.status,
            to_status=inv.status,
            metadata={
                "patch_candidate_id": str(patch_candidate.id),
                "regression_test_id": str(regression_test.id),
                "patch_sha256": patch_sha256,
            },
        )
        await self.investigation_service.record_event(
            investigation_id=investigation_id,
            event_type=EventType.PATCH_APPLICATION_STARTED,
            from_status=inv.status,
            to_status=inv.status,
            metadata={"patch_candidate_id": str(patch_candidate.id)},
        )

        verification_id = uuid4()
        now = datetime.now(UTC)

        # 4. Fresh Ephemeral Workspace Extraction & Execution
        with tempfile.TemporaryDirectory(prefix="evida_patch_verify_") as tmp_dir:
            repo_root = extract_archive_safely(archive_bytes, Path(tmp_dir), self.settings)

            # Step A: Apply Patch
            app_result, manifest_after = apply_patch_to_workspace(
                repo_root=repo_root,
                patch_content=patch_candidate.patch_content,
                declared_changed_files=patch_candidate.changed_files,
                timeout_seconds=self.settings.PATCH_APPLICATION_TIMEOUT_SECONDS,
            )

            if app_result.status != "APPLIED":
                await self.investigation_service.record_event(
                    investigation_id=investigation_id,
                    event_type=EventType.PATCH_APPLICATION_FAILED,
                    from_status=inv.status,
                    to_status=inv.status,
                    metadata={"error": app_result.stderr},
                )
                await self.investigation_service.record_event(
                    investigation_id=investigation_id,
                    event_type=EventType.PATCH_UNVERIFIED,
                    from_status=inv.status,
                    to_status=inv.status,
                    metadata={"reason": "PATCH_APPLICATION_FAILED", "details": app_result.stderr},
                )

                classification = (
                    VerificationFailureClassification.UNEXPECTED_WORKSPACE_CHANGE
                    if "unexpected" in app_result.stderr.lower()
                    else VerificationFailureClassification.PATCH_APPLICATION_FAILED
                )

                failed_run = PatchVerificationRun(
                    id=verification_id,
                    investigation_id=investigation_id,
                    patch_candidate_id=patch_candidate.id,
                    regression_test_id=regression_test.id,
                    status=PatchVerificationStatus.UNVERIFIED,
                    patch_sha256=patch_sha256,
                    repository_sha256=sha256_before,
                    patch_application_status=app_result.status,
                    patch_application_exit_code=app_result.exit_code,
                    patch_application_stdout=app_result.stdout,
                    patch_application_stderr=app_result.stderr,
                    regression_status="SKIPPED",
                    regression_exit_code=None,
                    regression_stdout="",
                    regression_stderr="Regression skipped due to patch application failure.",
                    regression_duration_ms=0,
                    baseline_status="SKIPPED",
                    baseline_command="pytest",
                    baseline_exit_code=None,
                    baseline_stdout="",
                    baseline_stderr="Baseline suite skipped due to patch application failure.",
                    baseline_duration_ms=0,
                    verdict=PatchVerificationVerdict.UNVERIFIED,
                    failure_classification=classification,
                    workspace_file_manifest=manifest_after,
                    created_at=now,
                    completed_at=datetime.now(UTC),
                )
                saved_run = await self.repo.save_patch_verification_run(failed_run)
                return self._to_response(saved_run)

            await self.investigation_service.record_event(
                investigation_id=investigation_id,
                event_type=EventType.PATCH_APPLICATION_COMPLETED,
                from_status=inv.status,
                to_status=inv.status,
                metadata={"modified_files": app_result.modified_files},
            )

            # Step B: Regression Test Verification (Validation 1)
            reg_dest = repo_root / regression_test.test_path
            reg_dest.parent.mkdir(parents=True, exist_ok=True)
            reg_dest.write_text(regression_test.test_content, encoding="utf-8")

            reg_raw = execute_command(
                ["pytest", regression_test.test_path],
                cwd=str(repo_root),
                timeout_seconds=self.settings.REGRESSION_VERIFICATION_TIMEOUT_SECONDS,
            )

            regression_passed = reg_raw.exit_code == 0 and not reg_raw.timed_out
            regression_status = (
                "PASSED" if regression_passed else ("TIMEOUT" if reg_raw.timed_out else "FAILED")
            )

            if not regression_passed:
                await self.investigation_service.record_event(
                    investigation_id=investigation_id,
                    event_type=EventType.REGRESSION_VERIFICATION_FAILED,
                    from_status=inv.status,
                    to_status=inv.status,
                    metadata={"exit_code": reg_raw.exit_code, "timed_out": reg_raw.timed_out},
                )
                await self.investigation_service.record_event(
                    investigation_id=investigation_id,
                    event_type=EventType.PATCH_UNVERIFIED,
                    from_status=inv.status,
                    to_status=inv.status,
                    metadata={
                        "reason": "REGRESSION_STILL_FAILING",
                        "exit_code": reg_raw.exit_code,
                    },
                )

                if reg_raw.timed_out:
                    reg_classification = VerificationFailureClassification.REGRESSION_TIMEOUT
                elif reg_raw.exit_code == 1:
                    reg_classification = VerificationFailureClassification.REGRESSION_STILL_FAILING
                else:
                    reg_classification = (
                        VerificationFailureClassification.REGRESSION_EXECUTION_ERROR
                    )

                failed_reg_run = PatchVerificationRun(
                    id=verification_id,
                    investigation_id=investigation_id,
                    patch_candidate_id=patch_candidate.id,
                    regression_test_id=regression_test.id,
                    status=PatchVerificationStatus.UNVERIFIED,
                    patch_sha256=patch_sha256,
                    repository_sha256=sha256_before,
                    patch_application_status=app_result.status,
                    patch_application_exit_code=app_result.exit_code,
                    patch_application_stdout=app_result.stdout,
                    patch_application_stderr=app_result.stderr,
                    regression_status=regression_status,
                    regression_exit_code=reg_raw.exit_code,
                    regression_stdout=reg_raw.stdout,
                    regression_stderr=reg_raw.stderr,
                    regression_duration_ms=int(reg_raw.duration_ms),
                    baseline_status="SKIPPED",
                    baseline_command="pytest",
                    baseline_exit_code=None,
                    baseline_stdout="",
                    baseline_stderr="Baseline suite skipped due to regression test failure.",
                    baseline_duration_ms=0,
                    verdict=PatchVerificationVerdict.UNVERIFIED,
                    failure_classification=reg_classification,
                    workspace_file_manifest=manifest_after,
                    created_at=now,
                    completed_at=datetime.now(UTC),
                )
                saved_run = await self.repo.save_patch_verification_run(failed_reg_run)
                return self._to_response(saved_run)

            await self.investigation_service.record_event(
                investigation_id=investigation_id,
                event_type=EventType.REGRESSION_VERIFICATION_PASSED,
                from_status=inv.status,
                to_status=inv.status,
                metadata={"exit_code": reg_raw.exit_code, "duration_ms": reg_raw.duration_ms},
            )

            # Step C: Baseline Test Suite Verification (Validation 2)
            # Remove injected regression test file so baseline suite runs original repository tests
            if reg_dest.exists():
                reg_dest.unlink()

            await self.investigation_service.record_event(
                investigation_id=investigation_id,
                event_type=EventType.BASELINE_VERIFICATION_STARTED,
                from_status=inv.status,
                to_status=inv.status,
                metadata={"command": "pytest"},
            )

            base_raw = execute_command(
                ["pytest"],
                cwd=str(repo_root),
                timeout_seconds=self.settings.BASELINE_VERIFICATION_TIMEOUT_SECONDS,
            )

            baseline_passed = base_raw.exit_code == 0 and not base_raw.timed_out
            baseline_status = (
                "PASSED" if baseline_passed else ("TIMEOUT" if base_raw.timed_out else "FAILED")
            )

            if not baseline_passed:
                await self.investigation_service.record_event(
                    investigation_id=investigation_id,
                    event_type=EventType.BASELINE_VERIFICATION_FAILED,
                    from_status=inv.status,
                    to_status=inv.status,
                    metadata={"exit_code": base_raw.exit_code, "timed_out": base_raw.timed_out},
                )
                await self.investigation_service.record_event(
                    investigation_id=investigation_id,
                    event_type=EventType.PATCH_UNVERIFIED,
                    from_status=inv.status,
                    to_status=inv.status,
                    metadata={"reason": "BASELINE_TEST_FAILURE", "exit_code": base_raw.exit_code},
                )

                if base_raw.timed_out:
                    base_classification = VerificationFailureClassification.BASELINE_TIMEOUT
                elif base_raw.exit_code == 1:
                    base_classification = VerificationFailureClassification.BASELINE_TEST_FAILURE
                else:
                    base_classification = VerificationFailureClassification.BASELINE_EXECUTION_ERROR

                failed_base_run = PatchVerificationRun(
                    id=verification_id,
                    investigation_id=investigation_id,
                    patch_candidate_id=patch_candidate.id,
                    regression_test_id=regression_test.id,
                    status=PatchVerificationStatus.UNVERIFIED,
                    patch_sha256=patch_sha256,
                    repository_sha256=sha256_before,
                    patch_application_status=app_result.status,
                    patch_application_exit_code=app_result.exit_code,
                    patch_application_stdout=app_result.stdout,
                    patch_application_stderr=app_result.stderr,
                    regression_status=regression_status,
                    regression_exit_code=reg_raw.exit_code,
                    regression_stdout=reg_raw.stdout,
                    regression_stderr=reg_raw.stderr,
                    regression_duration_ms=int(reg_raw.duration_ms),
                    baseline_status=baseline_status,
                    baseline_command="pytest",
                    baseline_exit_code=base_raw.exit_code,
                    baseline_stdout=base_raw.stdout,
                    baseline_stderr=base_raw.stderr,
                    baseline_duration_ms=int(base_raw.duration_ms),
                    verdict=PatchVerificationVerdict.UNVERIFIED,
                    failure_classification=base_classification,
                    workspace_file_manifest=manifest_after,
                    created_at=now,
                    completed_at=datetime.now(UTC),
                )
                saved_run = await self.repo.save_patch_verification_run(failed_base_run)
                return self._to_response(saved_run)

            await self.investigation_service.record_event(
                investigation_id=investigation_id,
                event_type=EventType.BASELINE_VERIFICATION_PASSED,
                from_status=inv.status,
                to_status=inv.status,
                metadata={"exit_code": base_raw.exit_code, "duration_ms": base_raw.duration_ms},
            )

        # 5. Source Integrity Post-Check (Ensuring archive on disk was NEVER modified)
        sha256_after = hashlib.sha256(archive_bytes).hexdigest()
        if sha256_before != sha256_after:
            await self.investigation_service.record_event(
                investigation_id=investigation_id,
                event_type=EventType.SOURCE_INTEGRITY_VIOLATION,
                from_status=inv.status,
                to_status=inv.status,
                metadata={"before": sha256_before, "after": sha256_after},
            )
            await self.investigation_service.record_event(
                investigation_id=investigation_id,
                event_type=EventType.PATCH_UNVERIFIED,
                from_status=inv.status,
                to_status=inv.status,
                metadata={"reason": "SOURCE_INTEGRITY_VIOLATION"},
            )
            integrity_run = PatchVerificationRun(
                id=verification_id,
                investigation_id=investigation_id,
                patch_candidate_id=patch_candidate.id,
                regression_test_id=regression_test.id,
                status=PatchVerificationStatus.UNVERIFIED,
                patch_sha256=patch_sha256,
                repository_sha256=sha256_before,
                patch_application_status=app_result.status,
                patch_application_exit_code=app_result.exit_code,
                patch_application_stdout=app_result.stdout,
                patch_application_stderr=app_result.stderr,
                regression_status=regression_status,
                regression_exit_code=reg_raw.exit_code,
                regression_stdout=reg_raw.stdout,
                regression_stderr=reg_raw.stderr,
                regression_duration_ms=int(reg_raw.duration_ms),
                baseline_status=baseline_status,
                baseline_command="pytest",
                baseline_exit_code=base_raw.exit_code,
                baseline_stdout=base_raw.stdout,
                baseline_stderr=base_raw.stderr,
                baseline_duration_ms=int(base_raw.duration_ms),
                verdict=PatchVerificationVerdict.UNVERIFIED,
                failure_classification=VerificationFailureClassification.SOURCE_INTEGRITY_VIOLATION,
                workspace_file_manifest=manifest_after,
                created_at=now,
                completed_at=datetime.now(UTC),
            )
            saved_run = await self.repo.save_patch_verification_run(integrity_run)
            return self._to_response(saved_run)

        await self.investigation_service.record_event(
            investigation_id=investigation_id,
            event_type=EventType.SOURCE_INTEGRITY_CHECKED,
            from_status=inv.status,
            to_status=inv.status,
            metadata={"sha256": sha256_after},
        )

        # 6. Success: Both test suites passed and source integrity confirmed
        # Transition lifecycle: VERIFYING -> COMPLETED
        await self.investigation_service.transition_investigation(
            investigation_id=investigation_id,
            target_status=InvestigationStatus.COMPLETED,
            event_type=EventType.PATCH_VERIFIED,
            metadata={
                "patch_candidate_id": str(patch_candidate.id),
                "regression_test_id": str(regression_test.id),
                "verdict": "VERIFIED",
            },
        )

        verified_run = PatchVerificationRun(
            id=verification_id,
            investigation_id=investigation_id,
            patch_candidate_id=patch_candidate.id,
            regression_test_id=regression_test.id,
            status=PatchVerificationStatus.VERIFIED,
            patch_sha256=patch_sha256,
            repository_sha256=sha256_before,
            patch_application_status=app_result.status,
            patch_application_exit_code=app_result.exit_code,
            patch_application_stdout=app_result.stdout,
            patch_application_stderr=app_result.stderr,
            regression_status=regression_status,
            regression_exit_code=reg_raw.exit_code,
            regression_stdout=reg_raw.stdout,
            regression_stderr=reg_raw.stderr,
            regression_duration_ms=int(reg_raw.duration_ms),
            baseline_status=baseline_status,
            baseline_command="pytest",
            baseline_exit_code=base_raw.exit_code,
            baseline_stdout=base_raw.stdout,
            baseline_stderr=base_raw.stderr,
            baseline_duration_ms=int(base_raw.duration_ms),
            verdict=PatchVerificationVerdict.VERIFIED,
            failure_classification=None,
            workspace_file_manifest=manifest_after,
            created_at=now,
            completed_at=datetime.now(UTC),
        )
        saved_run = await self.repo.save_patch_verification_run(verified_run)
        return self._to_response(saved_run)

    async def get_latest_verification(self, investigation_id: UUID) -> PatchVerificationResponse:
        """Retrieve latest verification evidence record for an investigation."""
        inv = await self.repo.get_by_id(investigation_id)
        if inv is None:
            raise InvestigationNotFoundError(str(investigation_id))

        run = await self.repo.get_patch_verification_run_by_investigation_id(investigation_id)
        if run is None:
            raise LifecycleException(
                f"No patch verification run found for investigation '{investigation_id}'.",
                code="VERIFICATION_RUN_NOT_FOUND",
                status_code=404,
            )
        return self._to_response(run)

    async def list_verifications(self, investigation_id: UUID) -> list[PatchVerificationResponse]:
        """Retrieve all verification runs for an investigation."""
        inv = await self.repo.get_by_id(investigation_id)
        if inv is None:
            raise InvestigationNotFoundError(str(investigation_id))

        runs = await self.repo.get_patch_verification_runs_by_investigation_id(investigation_id)
        return [self._to_response(r) for r in runs]

    def _to_response(self, run: PatchVerificationRun) -> PatchVerificationResponse:
        return PatchVerificationResponse(
            id=run.id,
            investigation_id=run.investigation_id,
            patch_candidate_id=run.patch_candidate_id,
            regression_test_id=run.regression_test_id,
            status=run.status,
            verdict=run.verdict,
            failure_classification=run.failure_classification,
            patch_sha256=run.patch_sha256,
            repository_sha256=run.repository_sha256,
            patch_application=PatchApplicationResponse(
                status=run.patch_application_status,
                exit_code=run.patch_application_exit_code,
                stdout=run.patch_application_stdout,
                stderr=run.patch_application_stderr,
                duration_ms=0.0,
                modified_files=list(run.workspace_file_manifest.keys()),
            ),
            regression_execution=VerificationTestResponse(
                status=run.regression_status,
                command=f"pytest {run.regression_test_id}",
                exit_code=run.regression_exit_code or 0,
                stdout=run.regression_stdout,
                stderr=run.regression_stderr,
                duration_ms=float(run.regression_duration_ms),
            ),
            baseline_execution=VerificationTestResponse(
                status=run.baseline_status,
                command=run.baseline_command,
                exit_code=run.baseline_exit_code or 0,
                stdout=run.baseline_stdout,
                stderr=run.baseline_stderr,
                duration_ms=float(run.baseline_duration_ms),
            ),
            workspace_file_manifest=run.workspace_file_manifest,
            source_integrity_verified=run.failure_classification
            != VerificationFailureClassification.SOURCE_INTEGRITY_VIOLATION,
            created_at=run.created_at,
            completed_at=run.completed_at,
        )
