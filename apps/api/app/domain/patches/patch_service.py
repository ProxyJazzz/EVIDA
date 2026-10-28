"""AI Patch Generation and Candidate Validation Domain Service (Phase 5)

Orchestrates synthesis of candidate unified diff patches using proven regression evidence,
validates syntax, test immutability, scope, and security, and persists the candidate patch.
CRITICAL INVARIANT: The patch is NOT executed or applied to the repository in Phase 5.
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from app.ai.client import AIProvider, AIProviderError
from app.ai.prompts import (
    PATCH_GENERATION_PROMPT_VERSION,
    PATCH_GENERATION_SYSTEM_PROMPT,
    build_patch_generation_user_prompt,
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
    RegressionVerificationStatus,
)
from app.domain.investigations.repository import InvestigationRepository
from app.domain.investigations.schemas import PatchCandidateResponse
from app.domain.investigations.service import InvestigationService
from app.domain.investigations.state_machine import LifecycleException
from app.domain.patches.models import (
    PatchCandidateRecord,
    PatchCandidateStatus,
    PatchProposal,
)
from app.domain.patches.patch_validator import validate_patch_proposal
from app.domain.repositories.archive_validator import extract_archive_safely
from app.domain.repositories.models import ReproductionRun, ReproductionStatus

logger = get_logger("evida.patches.service")


class PatchService:
    """Orchestrates AI candidate patch generation and deterministic validation."""

    def __init__(
        self,
        repo: InvestigationRepository,
        investigation_service: InvestigationService,
        ai_provider: AIProvider,
        settings: Settings,
    ) -> None:
        self.repo = repo
        self.investigation_service = investigation_service
        self.ai_provider = ai_provider
        self.settings = settings

    async def get_patch_candidate(
        self, investigation_id: UUID, user_id: str | None = None
    ) -> PatchCandidateResponse:
        """Retrieve the latest patch candidate for an investigation."""
        await self.investigation_service.get_investigation(investigation_id, user_id=user_id)

        patch = await self.repo.get_patch_candidate_by_investigation_id(investigation_id)
        if not patch:
            raise LifecycleException(
                f"No patch candidate found for investigation '{investigation_id}'.",
                code="PATCH_CANDIDATE_NOT_FOUND",
                status_code=404,
            )

        v_status = "NOT_VERIFIED"
        v_run = await self.repo.get_patch_verification_run_by_investigation_id(investigation_id)
        if v_run is not None:
            v_status = (
                v_run.verdict.value if hasattr(v_run.verdict, "value") else str(v_run.verdict)
            )

        return self._to_response(patch, verification_status=v_status)

    async def generate_and_validate_patch(
        self,
        investigation_id: UUID,
        force_regenerate: bool = False,
        user_id: str | None = None,
    ) -> PatchCandidateResponse:
        """Main Phase 5 entrypoint: assemble context, generate candidate patch, and validate.

        CRITICAL INVARIANT: The patch is NOT executed, verified, or applied in Phase 5.
        Source code remains completely unpatched and unmodified.
        """
        # 1. Precondition checks
        inv = await self.investigation_service.get_investigation(investigation_id, user_id=user_id)

        if inv.status != InvestigationStatus.VERIFYING:
            raise LifecycleException(
                f"Cannot generate patch: investigation must be in 'VERIFYING' status (current: '{inv.status}').",
                code="PATCH_PRECONDITION_FAILED",
                status_code=400,
            )

        repro_run = await self.repo.get_reproduction_run_by_investigation_id(investigation_id)
        if not repro_run or repro_run.status != ReproductionStatus.REPRODUCED:
            repro_status = repro_run.status if repro_run else "NONE"
            raise LifecycleException(
                f"Cannot generate patch: reproduction run must have status 'REPRODUCED' (current: '{repro_status}').",
                code="PATCH_PRECONDITION_FAILED",
                status_code=400,
            )

        hypothesis = await self.repo.get_hypothesis_by_investigation_id(investigation_id)
        if not hypothesis:
            raise LifecycleException(
                "Cannot generate patch without a validated Phase 3 hypothesis.",
                code="PATCH_PRECONDITION_FAILED",
                status_code=400,
            )

        regression_test = await self.repo.get_regression_test_by_investigation_id(investigation_id)
        if not regression_test:
            raise LifecycleException(
                "Cannot generate patch without a Phase 4 regression test.",
                code="PATCH_PRECONDITION_FAILED",
                status_code=400,
            )

        if regression_test.verification_status != RegressionVerificationStatus.REGRESSION_PROVEN:
            raise LifecycleException(
                f"Cannot generate patch: regression test must be proven (current: '{regression_test.verification_status}').",
                code="PATCH_PRECONDITION_FAILED",
                status_code=400,
            )

        # 2. Idempotency: Return existing validated patch if already generated
        existing_patch = await self.repo.get_patch_candidate_by_investigation_id(investigation_id)
        if (
            existing_patch
            and existing_patch.status == PatchCandidateStatus.VALIDATED
            and not force_regenerate
        ):
            logger.info(
                f"Patch candidate already generated and validated for investigation {investigation_id}",
                extra={"operation": "generate_patch", "status": "noop"},
            )
            return self._to_response(existing_patch)

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

        # 4. Record audit event: PATCH_GENERATION_STARTED
        await self.investigation_service.record_event(
            investigation_id=investigation_id,
            event_type=EventType.PATCH_GENERATION_STARTED,
            from_status=inv.status,
            to_status=inv.status,
            metadata={
                "hypothesis_id": str(hypothesis.id),
                "regression_test_id": str(regression_test.id),
            },
        )

        # 5. Extract unpatched repository in temporary read-only workspace to gather context
        verification_run = await self.repo.get_latest_verification_run_by_investigation_id(
            investigation_id
        )
        failure_output = verification_run.stdout if verification_run else ""

        with tempfile.TemporaryDirectory(prefix="evida_patch_context_") as tmp_dir:
            repo_root = extract_archive_safely(archive_bytes, Path(tmp_dir), self.settings)

            # Collect existing files relative to repo root
            existing_repo_files: set[str] = set()
            for path in repo_root.rglob("*"):
                if path.is_file():
                    existing_repo_files.add(path.relative_to(repo_root).as_posix())

            # Build bounded repository context
            context = build_investigation_context(
                repo_root=repo_root,
                stdout=repro_run.stdout,
                stderr=repro_run.stderr,
                settings=self.settings,
            )

            # 6. Generate patch proposal via AI
            proposal, raw_response, telemetry = await self._generate_patch_proposal(
                bug_description=inv.bug_description or "",
                repro_run=repro_run,
                hypothesis=hypothesis,
                regression_test=regression_test,
                failure_output=failure_output,
                tree=context.tree,
                source_files=context.source_files,
                test_files=context.test_files,
            )

            # 7. Deterministic Unified Diff & Scope/Security Validation
            allowed_affected_files = set(hypothesis.affected_files)
            if hypothesis.root_cause and hypothesis.root_cause.file:
                allowed_affected_files.add(hypothesis.root_cause.file)

            validation_result = validate_patch_proposal(
                proposal,
                self.settings,
                existing_repo_files=existing_repo_files,
                allowed_affected_files=allowed_affected_files,
            )

        # 8. Construct Persistent PatchCandidateRecord
        now = datetime.now(UTC)
        candidate_status = (
            PatchCandidateStatus.VALIDATED
            if validation_result.is_valid
            else PatchCandidateStatus.REJECTED
        )

        patch_record = PatchCandidateRecord(
            investigation_id=investigation_id,
            hypothesis_id=hypothesis.id,
            regression_test_id=regression_test.id,
            status=candidate_status,
            description=proposal.description,
            patch_format=proposal.patch_format,
            patch_content=proposal.patch_content,
            changed_files=proposal.changed_files,
            change_summary=[item.model_dump() for item in proposal.change_summary],
            reasoning=proposal.reasoning,
            validation_result=validation_result.classification.value,
            validation_errors=validation_result.errors,
            model=telemetry.get("model"),
            provider=telemetry.get("provider"),
            prompt_version=PATCH_GENERATION_PROMPT_VERSION,
            raw_response=raw_response,
            input_tokens=telemetry.get("input_tokens"),
            output_tokens=telemetry.get("output_tokens"),
            latency_ms=telemetry.get("latency_ms"),
            created_at=now,
            validated_at=now if validation_result.is_valid else None,
        )

        saved_patch = await self.repo.save_patch_candidate(patch_record)

        # 9. Audit Event Recording
        await self.investigation_service.record_event(
            investigation_id=investigation_id,
            event_type=EventType.PATCH_GENERATED,
            from_status=inv.status,
            to_status=inv.status,
            metadata={
                "patch_id": str(saved_patch.id),
                "changed_files": saved_patch.changed_files,
                "status": saved_patch.status.value,
            },
        )

        if validation_result.is_valid:
            await self.investigation_service.record_event(
                investigation_id=investigation_id,
                event_type=EventType.PATCH_VALIDATED,
                from_status=inv.status,
                to_status=inv.status,
                metadata={
                    "patch_id": str(saved_patch.id),
                    "classification": validation_result.classification.value,
                    "hunk_count": validation_result.hunk_count,
                },
            )
        else:
            await self.investigation_service.record_event(
                investigation_id=investigation_id,
                event_type=EventType.PATCH_REJECTED,
                from_status=inv.status,
                to_status=inv.status,
                metadata={
                    "patch_id": str(saved_patch.id),
                    "classification": validation_result.classification.value,
                    "errors": validation_result.errors,
                },
            )
            # Raise structured exception on validation failure for client visibility
            raise LifecycleException(
                f"Candidate patch rejected: {'; '.join(validation_result.errors)}",
                code=validation_result.classification.value,
                status_code=400,
            )

        # 10. Lifecycle remains in VERIFYING (Phase 5 does NOT transition to COMPLETED or FIXED)
        logger.info(
            f"Candidate patch successfully validated for investigation {investigation_id}",
            extra={
                "operation": "generate_patch",
                "status": "ok",
                "details": f"patch_id={saved_patch.id}",
            },
        )

        return self._to_response(saved_patch)

    async def _generate_patch_proposal(
        self,
        *,
        bug_description: str,
        repro_run: ReproductionRun,
        hypothesis: InvestigationHypothesisRecord,
        regression_test: InvestigationRegressionTestRecord,
        failure_output: str,
        tree: str,
        source_files: dict[str, str],
        test_files: dict[str, str],
    ) -> tuple[PatchProposal, dict[str, Any], dict[str, Any]]:
        """Invokes AI provider with structured prompt, parses JSON, and validates schema."""
        user_prompt = build_patch_generation_user_prompt(
            bug_description=bug_description,
            reproduction_command=repro_run.command,
            reproduction_stdout=repro_run.stdout,
            hypothesis=hypothesis.hypothesis,
            root_cause_file=hypothesis.root_cause.file,
            root_cause_symbol=hypothesis.root_cause.symbol,
            root_cause_description=hypothesis.root_cause.description,
            affected_files=hypothesis.affected_files,
            regression_test_path=regression_test.test_path,
            regression_test_content=regression_test.test_content,
            regression_failure_output=failure_output,
            tree=tree,
            source_files=source_files,
            test_files=test_files,
        )

        ai_response = await self._call_provider_with_retry(
            system_prompt=PATCH_GENERATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        raw_json = extract_json_payload(ai_response.content)
        try:
            parsed_data = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise LifecycleException(
                f"AI patch response is not valid JSON: {exc}",
                code="AI_RESPONSE_INVALID",
                status_code=502,
            ) from exc

        try:
            proposal = PatchProposal.model_validate(parsed_data)
        except Exception as exc:
            raise LifecycleException(
                f"AI patch response failed schema validation: {exc}",
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
        """Call AI provider with controlled single retry on transient network errors."""
        for attempt in (1, 2):
            try:
                return await self.ai_provider.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            except AIProviderError as exc:
                if attempt == 2:
                    raise LifecycleException(
                        f"AI provider failed to generate patch: {exc}",
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

    def _to_response(
        self,
        record: PatchCandidateRecord,
        verification_status: str = "NOT_VERIFIED",
    ) -> PatchCandidateResponse:
        """Format persistent entity record into API response."""
        return PatchCandidateResponse(
            id=record.id,
            investigation_id=record.investigation_id,
            hypothesis_id=record.hypothesis_id,
            regression_test_id=record.regression_test_id,
            status=record.status.value if hasattr(record.status, "value") else str(record.status),
            description=record.description,
            patch_format=record.patch_format,
            patch_content=record.patch_content,
            changed_files=record.changed_files,
            change_summary=record.change_summary,
            reasoning=record.reasoning,
            validation_result=str(record.validation_result) if record.validation_result else None,
            validation_errors=record.validation_errors,
            verification_status=verification_status,
            model=record.model,
            provider=record.provider,
            prompt_version=record.prompt_version,
            created_at=record.created_at,
            validated_at=record.validated_at,
        )
