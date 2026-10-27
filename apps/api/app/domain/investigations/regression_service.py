"""AI Regression Test Generation and Verification Domain Service (Phase 4)

Transforms Phase 3 causal hypotheses into executable pytest regression tests,
validates syntax/safety using Python AST, and deterministically verifies the test
against the unpatched repository in an isolated sandbox.
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sandbox.runner.runner import execute_command

from app.ai.client import AIProvider, AIProviderError
from app.ai.prompts import (
    REGRESSION_TEST_PROMPT_VERSION,
    REGRESSION_TEST_SYSTEM_PROMPT,
    build_regression_test_user_prompt,
)
from app.core.config import Settings
from app.core.logging import get_logger
from app.domain.investigations.ai_service import extract_json_payload
from app.domain.investigations.context_builder import build_investigation_context
from app.domain.investigations.models import (
    EventType,
    InvestigationHypothesisRecord,
    InvestigationRegressionTestRecord,
    InvestigationStatus,
    RegressionTestGenerationStatus,
    RegressionTestProposal,
    RegressionVerificationRun,
    RegressionVerificationStatus,
)
from app.domain.investigations.repository import InvestigationRepository
from app.domain.investigations.schemas import (
    RegressionTestResponse,
    RegressionVerificationResponse,
)
from app.domain.investigations.service import InvestigationService
from app.domain.investigations.state_machine import LifecycleException
from app.domain.investigations.test_validator import (
    validate_regression_test_proposal,
)
from app.domain.investigations.verdict_classifier import (
    classify_regression_test_verdict,
)
from app.domain.repositories.archive_validator import (
    extract_archive_safely,
)
from app.domain.repositories.models import ReproductionStatus

logger = get_logger("evida.investigations.regression_service")


class RegressionService:
    """Orchestrates AI regression test generation and deterministic sandbox verification."""

    def __init__(
        self,
        repository: InvestigationRepository,
        investigation_service: InvestigationService,
        ai_provider: AIProvider,
        settings: Settings,
    ) -> None:
        self.repo = repository
        self.investigation_service = investigation_service
        self.ai_provider = ai_provider
        self.settings = settings

    async def get_regression_test(self, investigation_id: UUID) -> RegressionTestResponse | None:
        """Retrieve the latest regression test and its verification result."""
        test_record = await self.repo.get_regression_test_by_investigation_id(investigation_id)
        if not test_record:
            return None

        verification_run = await self.repo.get_latest_verification_run_by_investigation_id(
            investigation_id
        )
        return self._to_response(test_record, verification_run)

    async def generate_and_verify_regression_test(
        self,
        investigation_id: UUID,
        force_regenerate: bool = False,
    ) -> RegressionTestResponse:
        """Main Phase 4 entrypoint: generate test, validate AST/path, and verify in sandbox.

        Idempotency:
            If a proven regression test already exists for this investigation and
            force_regenerate is False, returns the existing record immediately.
        """
        # 1. Precondition checks
        inv = await self.repo.get_by_id(investigation_id)
        if not inv:
            raise LifecycleException(
                f"Investigation '{investigation_id}' not found.",
                code="INVESTIGATION_NOT_FOUND",
                status_code=404,
            )

        if (
            inv.status != InvestigationStatus.INVESTIGATING
            and inv.status != InvestigationStatus.VERIFYING
        ):
            raise LifecycleException(
                f"Cannot generate regression test: investigation must be in 'INVESTIGATING' state, "
                f"currently in '{inv.status}'.",
                code="REGRESSION_PRECONDITION_FAILED",
                status_code=400,
            )

        repro_run = await self.repo.get_reproduction_run_by_investigation_id(investigation_id)
        if not repro_run or repro_run.status != ReproductionStatus.REPRODUCED:
            repro_status = repro_run.status if repro_run else "NONE"
            raise LifecycleException(
                f"Cannot generate regression test: reproduction run must have status 'REPRODUCED' "
                f"(current: '{repro_status}').",
                code="REGRESSION_PRECONDITION_FAILED",
                status_code=400,
            )

        hypothesis = await self.repo.get_hypothesis_by_investigation_id(investigation_id)
        if not hypothesis:
            raise LifecycleException(
                "Cannot generate regression test without a validated Phase 3 hypothesis.",
                code="REGRESSION_PRECONDITION_FAILED",
                status_code=400,
            )

        # 2. Check idempotency
        existing_test = await self.repo.get_regression_test_by_investigation_id(investigation_id)
        if (
            existing_test
            and existing_test.verification_status == RegressionVerificationStatus.REGRESSION_PROVEN
            and not force_regenerate
        ):
            latest_run = await self.repo.get_latest_verification_run_by_investigation_id(
                investigation_id
            )
            return self._to_response(existing_test, latest_run)

        # 3. Retrieve original repository archive
        repo_meta = await self.repo.get_repository_by_investigation_id(investigation_id)
        if not repo_meta or not repo_meta.storage_path:
            raise LifecycleException(
                "Repository archive metadata missing.",
                code="INVALID_ARCHIVE",
                status_code=400,
            )

        archive_bytes = await self.repo.get_archive_bytes(repo_meta.storage_path)
        if not archive_bytes:
            raise LifecycleException(
                "Repository archive payload missing from storage.",
                code="INVALID_ARCHIVE",
                status_code=400,
            )

        # 4. Generate structured regression test proposal via AI
        proposal, raw_response, telemetry = await self._generate_test_proposal(
            investigation=inv,
            reproduction=repro_run,
            hypothesis=hypothesis,
            archive_bytes=archive_bytes,
        )

        # 5. Deterministic AST and Path Validation
        validate_regression_test_proposal(
            test_path=proposal.test_path,
            test_content=proposal.test_content,
            max_bytes=self.settings.MAX_GENERATED_TEST_BYTES,
        )

        # 6. Persist generated regression test record
        test_record = InvestigationRegressionTestRecord(
            investigation_id=investigation_id,
            hypothesis_id=hypothesis.id,
            test_path=proposal.test_path,
            test_content=proposal.test_content,
            framework=proposal.framework,
            language=proposal.language,
            description=proposal.description,
            target_symbol=proposal.target_symbol,
            target_file=proposal.target_file,
            expected_failure_reason=proposal.expected_failure_reason,
            status=RegressionTestGenerationStatus.GENERATED,
            verification_status=RegressionVerificationStatus.PENDING,
            model=telemetry.get("model"),
            provider=telemetry.get("provider"),
            prompt_version=REGRESSION_TEST_PROMPT_VERSION,
            raw_response=raw_response,
            input_tokens=telemetry.get("input_tokens"),
            output_tokens=telemetry.get("output_tokens"),
            latency_ms=telemetry.get("latency_ms"),
        )
        saved_test = await self.repo.save_regression_test(test_record)

        await self.investigation_service.record_event(
            investigation_id=investigation_id,
            event_type=EventType.REGRESSION_TEST_GENERATED,
            from_status=inv.status,
            to_status=inv.status,
            metadata={
                "regression_test_id": str(saved_test.id),
                "test_path": saved_test.test_path,
                "target_symbol": saved_test.target_symbol,
                "framework": saved_test.framework,
            },
        )

        # 7. Verification: Run generated test in sandbox against unpatched repository
        verification_run = await self._verify_regression_test(
            investigation_id=investigation_id,
            test_record=saved_test,
            archive_bytes=archive_bytes,
        )

        # 8. Update test record with verification status
        saved_test.verification_status = verification_run.status
        saved_test.verification_run_id = verification_run.id
        saved_test.verified_at = verification_run.completed_at
        updated_test = await self.repo.save_regression_test(saved_test)

        # 9. Lifecycle Transition & Event Dispatching
        if verification_run.status == RegressionVerificationStatus.REGRESSION_PROVEN:
            if inv.status == InvestigationStatus.INVESTIGATING:
                await self.investigation_service.transition_investigation(
                    investigation_id=investigation_id,
                    target_status=InvestigationStatus.VERIFYING,
                    event_type=EventType.REGRESSION_TEST_PROVEN,
                    metadata={
                        "regression_test_id": str(updated_test.id),
                        "verification_run_id": str(verification_run.id),
                        "failure_classification": verification_run.failure_classification,
                    },
                )
            else:
                await self.investigation_service.record_event(
                    investigation_id=investigation_id,
                    event_type=EventType.REGRESSION_TEST_PROVEN,
                    from_status=inv.status,
                    to_status=inv.status,
                    metadata={"regression_test_id": str(updated_test.id)},
                )
        elif verification_run.status == RegressionVerificationStatus.TEST_REJECTED:
            await self.investigation_service.record_event(
                investigation_id=investigation_id,
                event_type=EventType.REGRESSION_TEST_REJECTED,
                from_status=inv.status,
                to_status=inv.status,
                metadata={
                    "regression_test_id": str(updated_test.id),
                    "reason": "Test passed against buggy repository without demonstrating defect",
                },
            )

        return self._to_response(updated_test, verification_run)

    async def _generate_test_proposal(
        self,
        investigation: Any,
        reproduction: Any,
        hypothesis: InvestigationHypothesisRecord,
        archive_bytes: bytes,
    ) -> tuple[RegressionTestProposal, dict[str, Any], dict[str, Any]]:
        """Construct prompt context, query AI provider, and parse structured proposal."""
        # Extract archive temporarily to build bounded repository context
        with tempfile.TemporaryDirectory(prefix="evida_regression_ctx_") as tmp_dir:
            repo_root = extract_archive_safely(archive_bytes, Path(tmp_dir), self.settings)
            context = build_investigation_context(
                repo_root=repo_root,
                stdout=reproduction.stdout or "",
                stderr=reproduction.stderr or "",
                settings=self.settings,
            )

        root_cause_file = (
            hypothesis.root_cause.file
            if hasattr(hypothesis.root_cause, "file")
            else str(hypothesis.root_cause)
        )
        root_cause_symbol = (
            hypothesis.root_cause.symbol if hasattr(hypothesis.root_cause, "symbol") else None
        )
        root_cause_desc = (
            hypothesis.root_cause.description
            if hasattr(hypothesis.root_cause, "description")
            else str(hypothesis.root_cause)
        )

        user_prompt = build_regression_test_user_prompt(
            bug_description=investigation.bug_description,
            reproduction_command=reproduction.command,
            execution_status=reproduction.status,
            exit_code=reproduction.exit_code,
            stdout=context.stdout,
            stderr=context.stderr,
            hypothesis=hypothesis.hypothesis,
            root_cause_file=root_cause_file,
            root_cause_symbol=root_cause_symbol,
            root_cause_description=root_cause_desc,
            affected_files=hypothesis.affected_files,
            evidence=hypothesis.evidence,
            tree=context.tree,
            source_files=context.source_files,
            test_files=context.test_files,
        )

        # Query provider with single retry on transient error
        ai_response = await self._call_provider_with_retry(
            system_prompt=REGRESSION_TEST_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # Extract and parse JSON
        raw_json = extract_json_payload(ai_response.content)
        try:
            parsed_data = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise LifecycleException(
                f"AI returned invalid JSON for regression test: {exc}",
                code="AI_RESPONSE_INVALID",
                status_code=502,
            ) from exc

        try:
            proposal = RegressionTestProposal(**parsed_data)
        except Exception as exc:
            raise LifecycleException(
                f"AI response failed regression test schema validation: {exc}",
                code="AI_RESPONSE_SCHEMA_INVALID",
                status_code=502,
            ) from exc

        telemetry: dict[str, Any] = {
            "model": ai_response.model,
            "provider": getattr(self.ai_provider, "provider_name", "nebius"),
            "latency_ms": int(ai_response.duration_ms) if ai_response.duration_ms else None,
            "input_tokens": ai_response.usage.prompt_tokens if ai_response.usage else None,
            "output_tokens": ai_response.usage.completion_tokens if ai_response.usage else None,
        }
        raw_response = {
            "content": ai_response.content,
            "finish_reason": ai_response.finish_reason,
        }

        return proposal, raw_response, telemetry

    async def _call_provider_with_retry(self, system_prompt: str, user_prompt: str) -> Any:
        for attempt in (1, 2):
            try:
                return await self.ai_provider.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            except AIProviderError as exc:
                if attempt == 2:
                    raise LifecycleException(
                        f"AI provider failed to generate regression test: {exc}",
                        code="AI_PROVIDER_UNAVAILABLE",
                        status_code=503,
                    ) from exc
                logger.warning(f"Transient AI provider error on attempt 1: {exc}")
            except Exception as exc:
                if attempt == 2:
                    raise LifecycleException(
                        f"AI provider communication error: {exc}",
                        code="AI_PROVIDER_UNAVAILABLE",
                        status_code=503,
                    ) from exc
                logger.warning(f"Unexpected error on attempt 1: {exc}")

    async def _verify_regression_test(
        self,
        investigation_id: UUID,
        test_record: InvestigationRegressionTestRecord,
        archive_bytes: bytes,
    ) -> RegressionVerificationRun:
        """Extract unpatched repository, write generated test, and execute in isolated sandbox."""
        await self.investigation_service.record_event(
            investigation_id=investigation_id,
            event_type=EventType.REGRESSION_TEST_VERIFICATION_STARTED,
            from_status=InvestigationStatus.INVESTIGATING,
            to_status=InvestigationStatus.INVESTIGATING,
            metadata={
                "regression_test_id": str(test_record.id),
                "test_path": test_record.test_path,
            },
        )

        verification_id = uuid4()
        now = datetime.now(UTC)
        command = f"pytest {test_record.test_path}"

        with tempfile.TemporaryDirectory(prefix="evida_regression_verify_") as tmp_dir:
            repo_root = extract_archive_safely(archive_bytes, Path(tmp_dir), self.settings)

            # Write generated test into workspace (ensuring directory structure exists)
            test_file_dest = repo_root / test_record.test_path
            test_file_dest.parent.mkdir(parents=True, exist_ok=True)
            test_file_dest.write_text(test_record.test_content, encoding="utf-8")

            # Execute via sandbox runner
            timeout = self.settings.REPRODUCTION_TIMEOUT_SECONDS
            raw_result = execute_command(
                ["pytest", test_record.test_path],
                timeout_seconds=timeout,
                cwd=str(repo_root),
            )

        completed_at = datetime.now(UTC)

        # Deterministically classify verdict
        verdict = classify_regression_test_verdict(
            exit_code=raw_result.exit_code,
            stdout=raw_result.stdout,
            stderr=raw_result.stderr,
            timed_out=raw_result.timed_out,
        )

        verification_run = RegressionVerificationRun(
            id=verification_id,
            investigation_id=investigation_id,
            regression_test_id=test_record.id,
            command=command,
            status=verdict.status,
            exit_code=raw_result.exit_code,
            stdout=raw_result.stdout,
            stderr=raw_result.stderr,
            duration_ms=int(raw_result.duration_ms),
            timed_out=raw_result.timed_out,
            failure_classification=verdict.failure_classification,
            created_at=now,
            completed_at=completed_at,
        )
        saved_run = await self.repo.save_regression_verification_run(verification_run)

        await self.investigation_service.record_event(
            investigation_id=investigation_id,
            event_type=EventType.REGRESSION_TEST_VERIFICATION_COMPLETED,
            from_status=InvestigationStatus.INVESTIGATING,
            to_status=InvestigationStatus.INVESTIGATING,
            metadata={
                "regression_test_id": str(test_record.id),
                "verification_run_id": str(saved_run.id),
                "status": saved_run.status,
                "failure_classification": saved_run.failure_classification,
                "exit_code": saved_run.exit_code,
            },
        )

        return saved_run

    def _to_response(
        self,
        test_record: InvestigationRegressionTestRecord,
        verification_run: RegressionVerificationRun | None,
    ) -> RegressionTestResponse:
        verification_resp = None
        if verification_run:
            verification_resp = RegressionVerificationResponse(
                id=verification_run.id,
                command=verification_run.command,
                status=str(verification_run.status),
                exit_code=verification_run.exit_code,
                duration_ms=verification_run.duration_ms,
                failure_classification=str(verification_run.failure_classification)
                if verification_run.failure_classification
                else None,
                stdout=verification_run.stdout,
                stderr=verification_run.stderr,
                timed_out=verification_run.timed_out,
                created_at=verification_run.created_at,
                completed_at=verification_run.completed_at,
            )

        return RegressionTestResponse(
            id=test_record.id,
            investigation_id=test_record.investigation_id,
            hypothesis_id=test_record.hypothesis_id,
            test_path=test_record.test_path,
            framework=test_record.framework,
            language=test_record.language,
            description=test_record.description,
            test_content=test_record.test_content,
            target_symbol=test_record.target_symbol,
            target_file=test_record.target_file,
            expected_failure_reason=test_record.expected_failure_reason,
            generation_status=str(test_record.status),
            verification_status=str(test_record.verification_status)
            if test_record.verification_status
            else None,
            model=test_record.model,
            provider=test_record.provider,
            prompt_version=test_record.prompt_version,
            verification=verification_resp,
            created_at=test_record.created_at,
            verified_at=test_record.verified_at,
        )
