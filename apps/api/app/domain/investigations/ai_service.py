"""AI Investigation and Causal Hypothesis Engine (Phase 3).

Coordinates bounded context building, structured prompt formulation,
NVIDIA/Nebius model invocation, hypothesis validation, and lifecycle transition.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.ai.client import AIProvider, AIProviderError
from app.ai.prompts import (
    INVESTIGATION_PROMPT_VERSION,
    INVESTIGATION_SYSTEM_PROMPT,
    build_investigation_user_prompt,
)
from app.core.config import Settings
from app.core.logging import get_logger
from app.domain.investigations.context_builder import build_investigation_context
from app.domain.investigations.models import (
    InvestigationHypothesis,
    InvestigationHypothesisRecord,
    InvestigationStatus,
)
from app.domain.investigations.repository import InvestigationRepository
from app.domain.investigations.schemas import InvestigationHypothesisResponse
from app.domain.investigations.service import InvestigationService
from app.domain.investigations.state_machine import LifecycleException
from app.domain.repositories.archive_validator import (
    extract_archive_safely,
)
from app.domain.repositories.models import ReproductionStatus

logger = get_logger("evida.investigations.ai_service")


def extract_json_payload(raw_text: str) -> str:
    """Extract raw JSON text from markdown code fences or unformatted model outputs."""
    trimmed = raw_text.strip()

    # Match ```json ... ``` or ``` ... ```
    fence_pattern = re.compile(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", re.IGNORECASE)
    match = fence_pattern.search(trimmed)
    if match:
        return match.group(1).strip()

    # Find outermost curly braces if fenced extraction wasn't present
    start = trimmed.find("{")
    end = trimmed.rfind("}")
    if start != -1 and end != -1 and end > start:
        return trimmed[start : end + 1]

    return trimmed


class AIInvestigationService:
    """Coordinates AI-driven software failure investigation and hypothesis generation."""

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

    async def investigate_failure(
        self,
        investigation_id: UUID,
        force_reinvestigate: bool = False,
        user_id: str | None = None,
    ) -> InvestigationHypothesisResponse:
        """Analyze deterministic failure evidence, formulate causal hypothesis, and advance to INVESTIGATING."""
        # 1. Retrieve investigation entity and verify ownership
        inv = await self.investigation_service.get_investigation(investigation_id, user_id=user_id)

        # 2. Precondition check: Investigation must be in REPRODUCING or INVESTIGATING
        if inv.status == InvestigationStatus.INVESTIGATING:
            # Idempotency: Return existing hypothesis if already generated
            existing_hypo = await self.repo.get_hypothesis_by_investigation_id(investigation_id)
            if existing_hypo and not force_reinvestigate:
                logger.info(
                    f"Investigation {investigation_id} already has a hypothesis, returning existing record",
                    extra={"operation": "investigate_failure", "status": "noop"},
                )
                return self._to_response(existing_hypo)

        if (
            inv.status != InvestigationStatus.REPRODUCING
            and inv.status != InvestigationStatus.INVESTIGATING
        ):
            raise LifecycleException(
                f"Cannot start AI investigation: Investigation status is '{inv.status}'. "
                "Investigation must be in 'REPRODUCING' status.",
                code="INVESTIGATION_PRECONDITION_FAILED",
                status_code=400,
            )

        # 3. Precondition check: Reproduction run must exist and have status REPRODUCED
        run = await self.repo.get_reproduction_run_by_investigation_id(investigation_id)
        if run is None:
            raise LifecycleException(
                "Cannot start AI investigation: No reproduction run exists for this investigation.",
                code="INVESTIGATION_PRECONDITION_FAILED",
                status_code=400,
            )

        if run.status != ReproductionStatus.REPRODUCED:
            raise LifecycleException(
                f"Cannot start AI investigation: Reproduction run status is '{run.status}'. "
                "AI investigation requires deterministic reproduction evidence (status 'REPRODUCED').",
                code="INVESTIGATION_PRECONDITION_FAILED",
                status_code=400,
            )

        # Idempotency check: if hypothesis exists for this exact reproduction run
        existing_hypo = await self.repo.get_hypothesis_by_investigation_id(investigation_id)
        if (
            existing_hypo
            and existing_hypo.reproduction_run_id == run.id
            and not force_reinvestigate
        ):
            return self._to_response(existing_hypo)

        # 4. Retrieve repository metadata and archive
        repo_meta = await self.repo.get_repository_by_investigation_id(investigation_id)
        if repo_meta is None or not repo_meta.storage_path:
            raise LifecycleException(
                "Repository archive record missing for this investigation.",
                code="REPOSITORY_NOT_FOUND",
                status_code=404,
            )

        archive_bytes = await self.repo.get_archive_bytes(repo_meta.storage_path)
        if not archive_bytes:
            raise LifecycleException(
                "Repository archive payload missing from storage.",
                code="AI_CONTEXT_BUILD_FAILED",
                status_code=500,
            )

        # 5. Extract to ephemeral workspace and build bounded context
        try:
            with tempfile.TemporaryDirectory(prefix="evida_ai_context_") as tmp_dir:
                repo_root = extract_archive_safely(archive_bytes, Path(tmp_dir), self.settings)
                context = build_investigation_context(
                    repo_root=repo_root,
                    stdout=run.stdout,
                    stderr=run.stderr,
                    settings=self.settings,
                )
        except Exception as exc:
            logger.error(f"Failed to build repository context: {exc}", exc_info=True)
            raise LifecycleException(
                f"Failed to build repository context for AI investigation: {exc}",
                code="AI_CONTEXT_BUILD_FAILED",
                status_code=500,
            ) from exc

        # 6. Construct structured investigation user prompt
        user_prompt = build_investigation_user_prompt(
            bug_description=inv.bug_description or inv.title,
            reproduction_command=run.command,
            execution_status=run.status.value,
            exit_code=run.exit_code,
            stdout=context.stdout,
            stderr=context.stderr,
            tree=context.tree,
            source_files=context.source_files,
            test_files=context.test_files,
        )

        # 7. Invoke AI Provider with at most 1 controlled retry on transient failures
        ai_response = await self._invoke_ai_with_retry(
            system_prompt=INVESTIGATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # 8. Parse and validate structured model output
        structured_hypothesis = self._parse_and_validate_response(ai_response.content)

        # 9. Persist hypothesis record
        hypo_id = uuid4()
        record = InvestigationHypothesisRecord(
            id=hypo_id,
            investigation_id=investigation_id,
            reproduction_run_id=run.id,
            model=ai_response.model,
            provider=ai_response.provider,
            hypothesis=structured_hypothesis.hypothesis,
            confidence=structured_hypothesis.confidence,
            root_cause=structured_hypothesis.root_cause,
            affected_files=structured_hypothesis.affected_files,
            evidence=structured_hypothesis.evidence,
            recommended_next_action=structured_hypothesis.recommended_next_action,
            raw_response={
                "content": ai_response.content,
                "finish_reason": ai_response.finish_reason,
            },
            prompt_version=INVESTIGATION_PROMPT_VERSION,
            input_tokens=ai_response.usage.prompt_tokens if ai_response.usage else None,
            output_tokens=ai_response.usage.completion_tokens if ai_response.usage else None,
            latency_ms=int(ai_response.duration_ms),
        )
        saved_record = await self.repo.save_hypothesis(record)

        # 10. Advance investigation lifecycle: REPRODUCING -> INVESTIGATING
        if inv.status == InvestigationStatus.REPRODUCING:
            await self.investigation_service.transition_investigation(
                investigation_id=investigation_id,
                target_status=InvestigationStatus.INVESTIGATING,
                event_type="INVESTIGATION_HYPOTHESIS_RECORDED",
                metadata={
                    "hypothesis_id": str(saved_record.id),
                    "model": saved_record.model,
                    "provider": saved_record.provider,
                    "confidence": saved_record.confidence,
                    "affected_files": saved_record.affected_files,
                    "root_cause_file": saved_record.root_cause.file,
                },
            )

        logger.info(
            f"AI hypothesis recorded for investigation {investigation_id}: {saved_record.hypothesis[:60]}...",
            extra={
                "operation": "investigate_failure",
                "status": "ok",
                "details": f"model={saved_record.model}, confidence={saved_record.confidence}",
            },
        )

        return self._to_response(saved_record)

    async def get_hypothesis(
        self, investigation_id: UUID, user_id: str | None = None
    ) -> InvestigationHypothesisResponse:
        """Retrieve the latest structured hypothesis for an investigation."""
        await self.investigation_service.get_investigation(investigation_id, user_id=user_id)

        record = await self.repo.get_hypothesis_by_investigation_id(investigation_id)
        if record is None:
            raise LifecycleException(
                f"No hypothesis found for investigation '{investigation_id}'.",
                code="HYPOTHESIS_NOT_FOUND",
                status_code=404,
            )
        return self._to_response(record)

    async def _invoke_ai_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Any:
        """Call AI provider with single controlled retry for transient network/server errors."""
        last_error: Exception | None = None

        for attempt in range(2):
            try:
                return await self.ai_provider.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            except AIProviderError as exc:
                last_error = exc
                # Do not retry 401/403 auth errors
                if exc.status_code in {401, 403}:
                    raise LifecycleException(
                        f"AI provider authentication failed: {exc.message}",
                        code="AI_PROVIDER_AUTHENTICATION_FAILED",
                        status_code=502,
                    ) from exc
                # If attempt 0, log and retry once for transient errors
                if attempt == 0:
                    logger.warning(f"Transient AI provider error on attempt 1, retrying: {exc}")
                    continue
            except Exception as exc:
                last_error = exc
                if attempt == 0:
                    logger.warning(f"Unexpected error on attempt 1, retrying: {exc}")
                    continue

        # If exhausted retries, map typed error
        err_msg = str(last_error) if last_error else "Unknown error"
        if "timed out" in err_msg.lower():
            raise LifecycleException(
                f"AI provider request timed out: {err_msg}",
                code="AI_PROVIDER_TIMEOUT",
                status_code=504,
            )
        raise LifecycleException(
            f"AI provider unavailable: {err_msg}",
            code="AI_PROVIDER_UNAVAILABLE",
            status_code=503,
        )

    def _parse_and_validate_response(self, raw_content: str) -> InvestigationHypothesis:
        """Parse raw content, extract JSON payload, and validate with Pydantic."""
        if not raw_content or not raw_content.strip():
            raise LifecycleException(
                "AI provider returned an empty response.",
                code="AI_RESPONSE_INVALID",
                status_code=502,
            )

        json_str = extract_json_payload(raw_content)

        try:
            parsed_data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse JSON from AI response: {exc}. Payload: {json_str[:300]}")
            raise LifecycleException(
                f"AI response is not valid JSON: {exc}",
                code="AI_RESPONSE_INVALID",
                status_code=502,
            ) from exc

        if not isinstance(parsed_data, dict):
            raise LifecycleException(
                "AI response JSON must be a top-level dictionary.",
                code="AI_RESPONSE_SCHEMA_INVALID",
                status_code=502,
            )

        try:
            return InvestigationHypothesis(**parsed_data)
        except Exception as exc:
            logger.error(f"AI response schema validation failed: {exc}. Data: {parsed_data}")
            raise LifecycleException(
                f"AI response schema validation failed: {exc}",
                code="AI_RESPONSE_SCHEMA_INVALID",
                status_code=502,
            ) from exc

    def _to_response(
        self, record: InvestigationHypothesisRecord
    ) -> InvestigationHypothesisResponse:
        return InvestigationHypothesisResponse(
            id=record.id,
            investigation_id=record.investigation_id,
            reproduction_run_id=record.reproduction_run_id,
            model=record.model,
            provider=record.provider,
            prompt_version=record.prompt_version,
            hypothesis=record.hypothesis,
            confidence=record.confidence,
            root_cause=record.root_cause,
            affected_files=record.affected_files,
            evidence=record.evidence,
            recommended_next_action=record.recommended_next_action,
            input_tokens=record.input_tokens,
            output_tokens=record.output_tokens,
            latency_ms=record.latency_ms,
            created_at=record.created_at,
        )
