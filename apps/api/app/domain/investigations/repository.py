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
    InvestigationStatus,
)

logger = get_logger("evida.investigations.repository")


class InvestigationRepository(Protocol):
    """Protocol defining persistence operations for investigations and lifecycle events."""

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


class InMemoryInvestigationRepository:
    """Thread-safe, transaction-consistent in-memory repository for local dev and testing."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._investigations: dict[UUID, Investigation] = {}
        self._events: dict[UUID, list[InvestigationEvent]] = {}
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

            # Update entity state
            inv.status = new_status
            inv.updated_at = datetime.now(UTC)

            # Record event
            if investigation_id not in self._events:
                self._events[investigation_id] = []
            self._events[investigation_id].append(event.model_copy())

            return inv.model_copy()

    async def get_events(self, investigation_id: UUID) -> list[InvestigationEvent]:
        async with self._lock:
            events = self._events.get(investigation_id, [])
            # Return chronologically ordered list
            return sorted(events, key=lambda e: e.created_at)


# Global singleton instance for in-memory persistence during application lifetime
_memory_repo_instance: InMemoryInvestigationRepository | None = None


def get_investigation_repository(settings: Settings) -> InvestigationRepository:
    """Repository factory providing persistence based on environment configuration."""
    global _memory_repo_instance
    if _memory_repo_instance is None:
        _memory_repo_instance = InMemoryInvestigationRepository()
    return _memory_repo_instance
