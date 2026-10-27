"""Investigation Persistence Layer

Provides protocol-based repository abstraction with in-memory implementation
for offline testing and development, and Supabase integration.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from app.core.config import Settings
from app.core.logging import get_logger
from app.domain.investigations.models import (
    EventType,
    Investigation,
    InvestigationEvent,
    InvestigationHypothesisRecord,
    InvestigationStatus,
)
from app.domain.repositories.models import (
    Repository,
    RepositoryStatus,
    ReproductionRun,
)

logger = get_logger("evida.investigations.repository")


class InvestigationRepository(Protocol):
    """Protocol defining persistence operations for investigations, archives, and reproduction runs."""

    async def get_by_id(self, investigation_id: UUID) -> Investigation | None:
        """Fetch investigation by UUID."""
        ...

    async def list_for_user(self, user_id: str) -> list[Investigation]:
        """Fetch all investigations belonging to a tenant/user."""
        ...

    async def create(
        self, investigation: Investigation, event: InvestigationEvent
    ) -> Investigation:
        """Atomically persist a new investigation and its creation event."""
        ...

    async def update_status_with_event(
        self,
        investigation_id: UUID,
        new_status: InvestigationStatus,
        event: InvestigationEvent,
    ) -> Investigation:
        """Atomically update status and record the lifecycle event."""
        ...

    async def get_events(self, investigation_id: UUID) -> list[InvestigationEvent]:
        """Fetch chronological timeline of lifecycle events for an investigation."""
        ...

    async def record_event(self, investigation_id: UUID, event: InvestigationEvent) -> None:
        """Append an audit event to the investigation timeline."""
        ...

    # Phase 2: Repository and Reproduction Persistence
    async def save_repository(self, repository: Repository) -> Repository:
        """Persist or update repository archive metadata."""
        ...

    async def get_repository_by_investigation_id(self, investigation_id: UUID) -> Repository | None:
        """Retrieve repository metadata associated with an investigation."""
        ...

    async def save_reproduction_run(self, run: ReproductionRun) -> ReproductionRun:
        """Persist or update a reproduction execution run."""
        ...

    async def get_reproduction_run_by_investigation_id(
        self, investigation_id: UUID
    ) -> ReproductionRun | None:
        """Retrieve latest reproduction run for an investigation."""
        ...

    async def save_archive_bytes(self, storage_path: str, data: bytes) -> None:
        """Store raw repository archive payload."""
        ...

    async def get_archive_bytes(self, storage_path: str) -> bytes | None:
        """Retrieve raw repository archive payload."""
        ...

    # Phase 3: AI Investigation Hypothesis Persistence
    async def save_hypothesis(
        self, hypothesis: InvestigationHypothesisRecord
    ) -> InvestigationHypothesisRecord:
        """Persist or update an AI investigation hypothesis record."""
        ...

    async def get_hypothesis_by_investigation_id(
        self, investigation_id: UUID
    ) -> InvestigationHypothesisRecord | None:
        """Retrieve latest AI investigation hypothesis for an investigation."""
        ...


class InMemoryInvestigationRepository:
    """Thread-safe, transaction-consistent in-memory repository for local dev and testing."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._investigations: dict[UUID, Investigation] = {}
        self._events: dict[UUID, list[InvestigationEvent]] = {}
        self._repositories: dict[UUID, Repository] = {}  # keyed by investigation_id
        self._repositories_by_id: dict[UUID, Repository] = {}
        self._reproduction_runs: dict[UUID, list[ReproductionRun]] = {}  # keyed by investigation_id
        self._hypotheses: dict[
            UUID, list[InvestigationHypothesisRecord]
        ] = {}  # keyed by investigation_id
        self._archives: dict[str, bytes] = {}
        self._seed_default_data()

    def _seed_default_data(self) -> None:
        """Seed initial record matching supabase/seed.sql."""
        demo_id = UUID("33333333-3333-3333-3333-333333333333")
        repo_id = UUID("22222222-2222-2222-2222-222222222222")
        proj_id = UUID("11111111-1111-1111-1111-111111111111")
        now = datetime.now(UTC)

        demo_inv = Investigation(
            id=demo_id,
            project_id=proj_id,
            repository_id=repo_id,
            title="Fix ZeroDivisionError in calculation endpoint",
            bug_description=(
                "When input denominator is 0, endpoint raises unhandled 500 "
                "ZeroDivisionError instead of returning 400 Bad Request."
            ),
            status=InvestigationStatus.CREATED,
            created_at=now,
            updated_at=now,
        )
        self._investigations[demo_id] = demo_inv

        demo_event = InvestigationEvent(
            id=UUID("44444444-4444-4444-4444-444444444444"),
            investigation_id=demo_id,
            event_type=EventType.INVESTIGATION_CREATED,
            from_status=None,
            to_status=InvestigationStatus.CREATED,
            metadata={"source": "seed_data"},
            created_at=now,
        )
        self._events[demo_id] = [demo_event]

        demo_repo = Repository(
            id=repo_id,
            investigation_id=demo_id,
            project_id=proj_id,
            name="demo-service.zip",
            storage_path="archives/33333333-3333-3333-3333-333333333333/demo-service.zip",
            archive_size_bytes=1024,
            archive_sha256="0000000000000000000000000000000000000000000000000000000000000000",
            status=RepositoryStatus.READY,
            created_at=now,
            updated_at=now,
        )
        self._repositories[demo_id] = demo_repo
        self._repositories_by_id[repo_id] = demo_repo

    async def get_by_id(self, investigation_id: UUID) -> Investigation | None:
        async with self._lock:
            inv = self._investigations.get(investigation_id)
            if inv is None:
                return None
            return inv.model_copy()

    async def list_for_user(self, user_id: str) -> list[Investigation]:
        async with self._lock:
            return [inv.model_copy() for inv in self._investigations.values()]

    async def create(
        self, investigation: Investigation, event: InvestigationEvent
    ) -> Investigation:
        async with self._lock:
            self._investigations[investigation.id] = investigation.model_copy()
            if investigation.id not in self._events:
                self._events[investigation.id] = []
            self._events[investigation.id].append(event.model_copy())
            return investigation.model_copy()

    async def update_status_with_event(
        self,
        investigation_id: UUID,
        new_status: InvestigationStatus,
        event: InvestigationEvent,
    ) -> Investigation:
        async with self._lock:
            inv = self._investigations.get(investigation_id)
            if inv is None:
                raise KeyError(f"Investigation {investigation_id} does not exist.")

            inv.status = new_status
            inv.updated_at = datetime.now(UTC)

            if investigation_id not in self._events:
                self._events[investigation_id] = []
            self._events[investigation_id].append(event.model_copy())

            return inv.model_copy()

    async def get_events(self, investigation_id: UUID) -> list[InvestigationEvent]:
        async with self._lock:
            events = self._events.get(investigation_id, [])
            return sorted(events, key=lambda e: e.created_at)

    async def record_event(self, investigation_id: UUID, event: InvestigationEvent) -> None:
        async with self._lock:
            if investigation_id not in self._events:
                self._events[investigation_id] = []
            self._events[investigation_id].append(event.model_copy())

    async def save_repository(self, repository: Repository) -> Repository:
        async with self._lock:
            if repository.investigation_id is not None:
                self._repositories[repository.investigation_id] = repository.model_copy()
            self._repositories_by_id[repository.id] = repository.model_copy()
            return repository.model_copy()

    async def get_repository_by_investigation_id(self, investigation_id: UUID) -> Repository | None:
        async with self._lock:
            repo = self._repositories.get(investigation_id)
            if repo is None:
                return None
            return repo.model_copy()

    async def save_reproduction_run(self, run: ReproductionRun) -> ReproductionRun:
        async with self._lock:
            if run.investigation_id not in self._reproduction_runs:
                self._reproduction_runs[run.investigation_id] = []
            # Replace if already exists with same ID, otherwise append
            existing = [r for r in self._reproduction_runs[run.investigation_id] if r.id == run.id]
            if existing:
                self._reproduction_runs[run.investigation_id] = [
                    run.model_copy() if r.id == run.id else r
                    for r in self._reproduction_runs[run.investigation_id]
                ]
            else:
                self._reproduction_runs[run.investigation_id].append(run.model_copy())
            return run.model_copy()

    async def get_reproduction_run_by_investigation_id(
        self, investigation_id: UUID
    ) -> ReproductionRun | None:
        async with self._lock:
            runs = self._reproduction_runs.get(investigation_id, [])
            if not runs:
                return None
            # Return latest run
            return runs[-1].model_copy()

    async def save_archive_bytes(self, storage_path: str, data: bytes) -> None:
        async with self._lock:
            self._archives[storage_path] = data

    async def get_archive_bytes(self, storage_path: str) -> bytes | None:
        async with self._lock:
            return self._archives.get(storage_path)

    async def save_hypothesis(
        self, hypothesis: InvestigationHypothesisRecord
    ) -> InvestigationHypothesisRecord:
        async with self._lock:
            if hypothesis.investigation_id not in self._hypotheses:
                self._hypotheses[hypothesis.investigation_id] = []
            existing = [
                h for h in self._hypotheses[hypothesis.investigation_id] if h.id == hypothesis.id
            ]
            if existing:
                self._hypotheses[hypothesis.investigation_id] = [
                    hypothesis.model_copy() if h.id == hypothesis.id else h
                    for h in self._hypotheses[hypothesis.investigation_id]
                ]
            else:
                self._hypotheses[hypothesis.investigation_id].append(hypothesis.model_copy())
            return hypothesis.model_copy()

    async def get_hypothesis_by_investigation_id(
        self, investigation_id: UUID
    ) -> InvestigationHypothesisRecord | None:
        async with self._lock:
            hypotheses = self._hypotheses.get(investigation_id, [])
            if not hypotheses:
                return None
            return hypotheses[-1].model_copy()


_memory_repo_instance: InMemoryInvestigationRepository | None = None


def get_investigation_repository(settings: Settings) -> InvestigationRepository:
    """Repository factory providing persistence based on environment configuration."""
    global _memory_repo_instance
    if _memory_repo_instance is None:
        _memory_repo_instance = InMemoryInvestigationRepository()
    return _memory_repo_instance
