"""Investigation Lifecycle Service

Orchestrates business logic, state transitions, event timelines, and repository persistence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.core.logging import get_logger
from app.domain.investigations.models import (
    EventType,
    Investigation,
    InvestigationEvent,
    InvestigationStatus,
)
from app.domain.investigations.repository import InvestigationRepository
from app.domain.investigations.schemas import (
    InvestigationCreate,
    InvestigationEventResponse,
    InvestigationEventsResponse,
    InvestigationListResponse,
    InvestigationResponse,
)
from app.domain.investigations.state_machine import (
    TERMINAL_STATES,
    InvestigationAlreadyTerminalError,
    InvestigationNotFoundError,
    validate_transition,
)

logger = get_logger("evida.investigations.service")


class InvestigationService:
    """Core domain service for EVIDA repair investigations."""

    def __init__(self, repository: InvestigationRepository) -> None:
        self.repo = repository

    async def create_investigation(
        self, request: InvestigationCreate, user_id: str
    ) -> InvestigationResponse:
        """Create a new investigation in CREATED status and emit creation event."""
        now = datetime.now(UTC)
        inv_id = uuid4()

        title = request.title or request.issue_title or "Untitled Investigation"
        description = request.bug_description or request.issue_description

        entity = Investigation(
            id=inv_id,
            project_id=request.project_id,
            repository_id=request.repository_id,
            title=title,
            bug_description=description,
            status=InvestigationStatus.CREATED,
            created_at=now,
            updated_at=now,
        )

        creation_event = InvestigationEvent(
            id=uuid4(),
            investigation_id=inv_id,
            event_type=EventType.INVESTIGATION_CREATED,
            from_status=None,
            to_status=InvestigationStatus.CREATED,
            metadata={
                "user_id": user_id,
                "repository_id": str(request.repository_id),
                "project_id": str(request.project_id) if request.project_id else None,
            },
            created_at=now,
        )

        persisted = await self.repo.create(entity, creation_event)
        logger.info(
            f"Investigation {inv_id} created with status CREATED",
            extra={
                "operation": "create_investigation",
                "status": "ok",
                "details": f"id={inv_id}",
            },
        )
        return self._to_response(persisted)

    async def get_investigation(self, investigation_id: UUID) -> InvestigationResponse:
        """Retrieve an investigation by UUID or raise InvestigationNotFoundError."""
        inv = await self.repo.get_by_id(investigation_id)
        if inv is None:
            raise InvestigationNotFoundError(str(investigation_id))
        return self._to_response(inv)

    async def start_investigation(self, investigation_id: UUID) -> InvestigationResponse:
        """Start investigation by transitioning from CREATED to INGESTING.

        Idempotency:
        - If currently in CREATED: transitions to INGESTING and emits INVESTIGATION_STARTED event.
        - If already INGESTING or beyond (non-terminal): returns current state safely without mutating or resetting.
        - If in a terminal state (COMPLETED, FAILED): raises InvestigationAlreadyTerminalError.
        """
        inv = await self.repo.get_by_id(investigation_id)
        if inv is None:
            raise InvestigationNotFoundError(str(investigation_id))

        # Check if already terminal
        if inv.status in TERMINAL_STATES:
            raise InvestigationAlreadyTerminalError(current_status=inv.status)

        # Idempotent safety: if already progressed beyond CREATED, return current state
        if inv.status != InvestigationStatus.CREATED:
            logger.info(
                f"Investigation {investigation_id} already in active state '{inv.status}', returning current state",
                extra={
                    "operation": "start_investigation",
                    "status": "noop",
                    "details": f"current_status={inv.status}",
                },
            )
            return self._to_response(inv)

        # Perform valid transition: CREATED -> INGESTING
        return await self.transition_investigation(
            investigation_id=investigation_id,
            target_status=InvestigationStatus.INGESTING,
            event_type=EventType.INVESTIGATION_STARTED,
            metadata={"trigger": "api_start"},
        )

    async def transition_investigation(
        self,
        investigation_id: UUID,
        target_status: InvestigationStatus,
        event_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> InvestigationResponse:
        """Validate state transition rules, record audit event, and atomically update state."""
        inv = await self.repo.get_by_id(investigation_id)
        if inv is None:
            raise InvestigationNotFoundError(str(investigation_id))

        # Enforce canonical transition constraints
        validate_transition(current_status=inv.status, target_status=target_status)

        # Determine semantic event type
        if event_type is None:
            if target_status == InvestigationStatus.COMPLETED:
                event_type = EventType.INVESTIGATION_COMPLETED
            elif target_status == InvestigationStatus.FAILED:
                event_type = EventType.INVESTIGATION_FAILED
            elif target_status == InvestigationStatus.INGESTING:
                event_type = EventType.INVESTIGATION_STARTED
            else:
                event_type = EventType.STATE_TRANSITIONED

        now = datetime.now(UTC)
        event = InvestigationEvent(
            id=uuid4(),
            investigation_id=investigation_id,
            event_type=event_type,
            from_status=inv.status,
            to_status=target_status,
            metadata=metadata or {},
            created_at=now,
        )

        updated = await self.repo.update_status_with_event(
            investigation_id=investigation_id,
            new_status=target_status,
            event=event,
        )

        logger.info(
            f"Investigation {investigation_id} transitioned: {inv.status} -> {target_status}",
            extra={
                "operation": "transition_investigation",
                "status": "ok",
                "details": f"from={inv.status}, to={target_status}",
            },
        )
        return self._to_response(updated)

    async def get_events(self, investigation_id: UUID) -> InvestigationEventsResponse:
        """Return ordered timeline of lifecycle events for an investigation."""
        inv = await self.repo.get_by_id(investigation_id)
        if inv is None:
            raise InvestigationNotFoundError(str(investigation_id))

        events = await self.repo.get_events(investigation_id)
        items = [
            InvestigationEventResponse(
                id=e.id,
                investigation_id=e.investigation_id,
                event_type=e.event_type,
                from_status=e.from_status,
                to_status=e.to_status,
                metadata=e.metadata,
                created_at=e.created_at,
            )
            for e in events
        ]
        return InvestigationEventsResponse(items=items, total=len(items))

    async def list_investigations(self, user_id: str) -> InvestigationListResponse:
        """List all investigations for user."""
        items = await self.repo.list_for_user(user_id)
        responses = [self._to_response(inv) for inv in items]
        return InvestigationListResponse(items=responses, total=len(responses))

    def _to_response(self, entity: Investigation) -> InvestigationResponse:
        return InvestigationResponse(
            id=entity.id,
            investigation_id=entity.id,
            project_id=entity.project_id,
            repository_id=entity.repository_id,
            title=entity.title,
            bug_description=entity.bug_description,
            status=entity.status,
            hypothesis=entity.hypothesis,
            regression_test_code=entity.regression_test_code,
            candidate_patch=entity.candidate_patch,
            verification_evidence=entity.verification_evidence,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
