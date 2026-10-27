"""Reproduction Service for Phase 2

Orchestrates secure ZIP ingestion, ephemeral workspace extraction, reproduction
command validation, isolated sandbox execution, and evidence persistence.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.core.config import Settings
from app.core.logging import get_logger
from app.domain.investigations.models import (
    InvestigationEvent,
    InvestigationStatus,
)
from app.domain.investigations.repository import InvestigationRepository
from app.domain.investigations.service import InvestigationService
from app.domain.investigations.state_machine import LifecycleException
from app.domain.repositories.archive_validator import (
    extract_archive_safely,
    validate_zip_archive,
)
from app.domain.repositories.command_validator import validate_reproduction_command
from app.domain.repositories.models import (
    Repository,
    RepositoryResponse,
    RepositoryStatus,
    ReproductionRun,
    ReproductionRunResponse,
    ReproductionStatus,
)

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sandbox.runner.runner import execute_command  # noqa: E402

logger = get_logger("evida.repositories.service")


class ReproductionService:
    """Service handling repository ingestion and failure reproduction pipeline."""

    def __init__(
        self,
        repository: InvestigationRepository,
        investigation_service: InvestigationService,
        settings: Settings,
    ) -> None:
        self.repo = repository
        self.investigation_service = investigation_service
        self.settings = settings

    async def ingest_repository_archive(
        self,
        investigation_id: UUID,
        filename: str,
        content: bytes,
    ) -> RepositoryResponse:
        """Validate and ingest a repository archive, advancing investigation state to INGESTING."""
        # 1. Verify investigation exists
        inv = await self.investigation_service.get_investigation(investigation_id)

        # 2. Securely validate archive prior to storing
        validated_meta = validate_zip_archive(content, filename, self.settings)

        # 3. Store archive bytes
        storage_path = f"archives/{investigation_id}/{filename}"
        await self.repo.save_archive_bytes(storage_path, content)

        # 4. Create or update Repository record
        existing_repo = await self.repo.get_repository_by_investigation_id(investigation_id)
        repo_id = existing_repo.id if existing_repo else uuid4()
        now = datetime.now(UTC)

        repo_record = Repository(
            id=repo_id,
            investigation_id=investigation_id,
            project_id=inv.project_id,
            name=filename,
            storage_path=storage_path,
            archive_size_bytes=validated_meta.size_bytes,
            archive_sha256=validated_meta.sha256_hash,
            status=RepositoryStatus.READY,
            created_at=existing_repo.created_at if existing_repo else now,
            updated_at=now,
        )
        saved_repo = await self.repo.save_repository(repo_record)

        # 5. Advance investigation lifecycle: CREATED -> INGESTING
        if inv.status == InvestigationStatus.CREATED:
            await self.investigation_service.transition_investigation(
                investigation_id=investigation_id,
                target_status=InvestigationStatus.INGESTING,
                event_type="REPOSITORY_INGESTED",
                metadata={
                    "repository_id": str(saved_repo.id),
                    "filename": filename,
                    "sha256": validated_meta.sha256_hash,
                    "size_bytes": validated_meta.size_bytes,
                },
            )

        logger.info(
            f"Repository archive '{filename}' ingested for investigation {investigation_id}",
            extra={
                "operation": "ingest_repository_archive",
                "status": "ok",
                "details": f"sha256={validated_meta.sha256_hash}",
            },
        )

        return RepositoryResponse(
            id=saved_repo.id,
            investigation_id=saved_repo.investigation_id,
            name=saved_repo.name,
            archive_size_bytes=saved_repo.archive_size_bytes,
            archive_sha256=saved_repo.archive_sha256,
            status=saved_repo.status,
            created_at=saved_repo.created_at,
            updated_at=saved_repo.updated_at,
        )

    async def get_repository(self, investigation_id: UUID) -> RepositoryResponse:
        """Fetch repository metadata for an investigation."""
        # Ensure investigation exists
        await self.investigation_service.get_investigation(investigation_id)

        repo = await self.repo.get_repository_by_investigation_id(investigation_id)
        if repo is None:
            raise LifecycleException(
                f"Repository not found for investigation '{investigation_id}'.",
                code="REPOSITORY_NOT_FOUND",
                status_code=404,
            )

        return RepositoryResponse(
            id=repo.id,
            investigation_id=repo.investigation_id,
            name=repo.name,
            archive_size_bytes=repo.archive_size_bytes,
            archive_sha256=repo.archive_sha256,
            status=repo.status,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
        )

    async def reproduce_failure(
        self,
        investigation_id: UUID,
        command: str,
        force_rerun: bool = False,
    ) -> ReproductionRunResponse:
        """Execute the reproduction command in an isolated ephemeral workspace and persist evidence."""
        inv = await self.investigation_service.get_investigation(investigation_id)

        repo_meta = await self.repo.get_repository_by_investigation_id(investigation_id)
        if repo_meta is None or not repo_meta.storage_path:
            raise LifecycleException(
                "Cannot reproduce failure: No repository uploaded for this investigation.",
                code="REPOSITORY_NOT_FOUND",
                status_code=404,
            )

        # Idempotency check: return existing running or completed run if not forcing rerun
        existing_run = await self.repo.get_reproduction_run_by_investigation_id(investigation_id)
        if existing_run:
            if existing_run.status == ReproductionStatus.RUNNING:
                return self._to_run_response(existing_run)
            if not force_rerun and existing_run.status in {
                ReproductionStatus.REPRODUCED,
                ReproductionStatus.NOT_REPRODUCED,
            }:
                return self._to_run_response(existing_run)

        # 1. Validate reproduction command safely
        parsed_cmd = validate_reproduction_command(command)

        # 2. Retrieve archive bytes
        archive_bytes = await self.repo.get_archive_bytes(repo_meta.storage_path)
        if not archive_bytes:
            raise LifecycleException(
                "Repository archive payload missing from storage.",
                code="INVALID_ARCHIVE",
                status_code=400,
            )

        # 3. Transition investigation: INGESTING -> REPRODUCING (if currently INGESTING)
        if inv.status == InvestigationStatus.INGESTING:
            await self.investigation_service.transition_investigation(
                investigation_id=investigation_id,
                target_status=InvestigationStatus.REPRODUCING,
                event_type="REPRODUCTION_STARTED",
                metadata={"command": command, "repository_id": str(repo_meta.id)},
            )

        # 4. Create PENDING/RUNNING ReproductionRun
        run_id = uuid4()
        now = datetime.now(UTC)
        run_record = ReproductionRun(
            id=run_id,
            investigation_id=investigation_id,
            repository_id=repo_meta.id,
            command=command,
            status=ReproductionStatus.RUNNING,
            created_at=now,
        )
        await self.repo.save_reproduction_run(run_record)

        # 5. Ephemeral sandbox execution boundary
        try:
            with tempfile.TemporaryDirectory(prefix="evida_ephemeral_workspace_") as tmp_dir:
                repo_root = extract_archive_safely(archive_bytes, Path(tmp_dir), self.settings)

                # Execute inside isolated sandbox runner
                timeout = self.settings.REPRODUCTION_TIMEOUT_SECONDS
                raw_result = execute_command(
                    parsed_cmd,
                    timeout_seconds=timeout,
                    cwd=str(repo_root),
                )

            completed_at = datetime.now(UTC)

            # 6. Classify reproduction verdict (Section 13)
            if raw_result.timed_out:
                verdict = ReproductionStatus.TIMEOUT
            elif raw_result.exit_code == 0:
                verdict = ReproductionStatus.NOT_REPRODUCED
            elif raw_result.exit_code > 0:
                verdict = ReproductionStatus.REPRODUCED
            else:
                verdict = ReproductionStatus.EXECUTION_ERROR

            # 7. Update and persist evidence
            run_record.exit_code = raw_result.exit_code
            run_record.stdout = raw_result.stdout
            run_record.stderr = raw_result.stderr
            run_record.duration_ms = int(raw_result.duration_ms)
            run_record.timed_out = raw_result.timed_out
            run_record.status = verdict
            run_record.completed_at = completed_at

            saved_run = await self.repo.save_reproduction_run(run_record)

            # 8. Record audit event
            event = InvestigationEvent(
                id=uuid4(),
                investigation_id=investigation_id,
                event_type="REPRODUCTION_EVIDENCE_RECORDED",
                from_status=InvestigationStatus.REPRODUCING,
                to_status=InvestigationStatus.REPRODUCING,
                metadata={
                    "run_id": str(saved_run.id),
                    "verdict": verdict.value,
                    "exit_code": saved_run.exit_code,
                    "duration_ms": saved_run.duration_ms,
                    "timed_out": saved_run.timed_out,
                    "command": command,
                },
                created_at=completed_at,
            )
            # Append event atomically to history
            await self.repo.record_event(investigation_id, event)

            logger.info(
                f"Reproduction run completed for investigation {investigation_id}: {verdict}",
                extra={
                    "operation": "reproduce_failure",
                    "status": "ok",
                    "details": f"verdict={verdict}, exit_code={raw_result.exit_code}",
                },
            )

            return self._to_run_response(saved_run)

        except Exception as exc:
            run_record.status = ReproductionStatus.EXECUTION_ERROR
            run_record.stderr = f"Sandbox execution setup error: {exc}"
            run_record.completed_at = datetime.now(UTC)
            await self.repo.save_reproduction_run(run_record)
            logger.error(
                f"Reproduction failure setup error: {exc}",
                exc_info=True,
                extra={"operation": "reproduce_failure", "status": "error"},
            )
            return self._to_run_response(run_record)

    async def get_reproduction(self, investigation_id: UUID) -> ReproductionRunResponse:
        """Fetch latest reproduction run result for an investigation."""
        await self.investigation_service.get_investigation(investigation_id)

        run = await self.repo.get_reproduction_run_by_investigation_id(investigation_id)
        if run is None:
            raise LifecycleException(
                f"No reproduction run found for investigation '{investigation_id}'.",
                code="REPRODUCTION_NOT_FOUND",
                status_code=404,
            )
        return self._to_run_response(run)

    def _to_run_response(self, run: ReproductionRun) -> ReproductionRunResponse:
        return ReproductionRunResponse(
            id=run.id,
            investigation_id=run.investigation_id,
            repository_id=run.repository_id,
            command=run.command,
            status=run.status,
            exit_code=run.exit_code,
            stdout=run.stdout,
            stderr=run.stderr,
            duration_ms=run.duration_ms,
            timed_out=run.timed_out,
            created_at=run.created_at,
            completed_at=run.completed_at,
        )
