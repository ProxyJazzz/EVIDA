"""Unit tests for InvestigationService and event timeline."""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.domain.investigations.models import EventType, InvestigationStatus
from app.domain.investigations.repository import InMemoryInvestigationRepository
from app.domain.investigations.schemas import InvestigationCreate
from app.domain.investigations.service import InvestigationService
from app.domain.investigations.state_machine import (
    InvalidStateTransitionError,
    InvestigationAlreadyTerminalError,
    InvestigationNotFoundError,
)


@pytest.fixture
def clean_service() -> InvestigationService:
    repo = InMemoryInvestigationRepository()
    # Reset internal stores for test isolation
    repo._investigations.clear()
    repo._events.clear()
    return InvestigationService(repo)


@pytest.mark.asyncio
async def test_create_investigation_emits_event(clean_service: InvestigationService):
    repo_id = uuid4()
    proj_id = uuid4()
    req = InvestigationCreate(
        repository_id=repo_id,
        project_id=proj_id,
        title="Null pointer in auth handler",
        bug_description="Token is None when unauthenticated request arrives",
    )

    created = await clean_service.create_investigation(req, user_id="user-123")
    assert created.status == InvestigationStatus.CREATED
    assert created.title == "Null pointer in auth handler"
    assert created.repository_id == repo_id
    assert created.project_id == proj_id

    # Check that INVESTIGATION_CREATED event was generated
    events_resp = await clean_service.get_events(created.id)
    assert events_resp.total == 1
    ev = events_resp.items[0]
    assert ev.event_type == EventType.INVESTIGATION_CREATED
    assert ev.from_status is None
    assert ev.to_status == InvestigationStatus.CREATED
    assert ev.investigation_id == created.id


@pytest.mark.asyncio
async def test_start_investigation_lifecycle(clean_service: InvestigationService):
    req = InvestigationCreate(
        repository_id=uuid4(),
        title="Divide by zero error",
    )
    inv = await clean_service.create_investigation(req, user_id="user-123")

    # Start investigation: CREATED -> INGESTING
    started = await clean_service.start_investigation(inv.id)
    assert started.status == InvestigationStatus.INGESTING

    # Verify event timeline has 2 events in chronological order
    events_resp = await clean_service.get_events(inv.id)
    assert events_resp.total == 2
    assert events_resp.items[0].event_type == EventType.INVESTIGATION_CREATED
    assert events_resp.items[1].event_type == EventType.INVESTIGATION_STARTED
    assert events_resp.items[1].from_status == InvestigationStatus.CREATED
    assert events_resp.items[1].to_status == InvestigationStatus.INGESTING
    assert events_resp.items[0].created_at <= events_resp.items[1].created_at


@pytest.mark.asyncio
async def test_start_investigation_idempotency(clean_service: InvestigationService):
    req = InvestigationCreate(
        repository_id=uuid4(),
        title="Flaky network timeout",
    )
    inv = await clean_service.create_investigation(req, user_id="user-123")
    started1 = await clean_service.start_investigation(inv.id)
    assert started1.status == InvestigationStatus.INGESTING

    # Repeated start must NOT raise error, reset, or duplicate events
    started2 = await clean_service.start_investigation(inv.id)
    assert started2.status == InvestigationStatus.INGESTING
    assert started2.id == inv.id

    # Event count must remain 2 (creation + start)
    events_resp = await clean_service.get_events(inv.id)
    assert events_resp.total == 2


@pytest.mark.asyncio
async def test_full_lifecycle_walkthrough(clean_service: InvestigationService):
    req = InvestigationCreate(
        repository_id=uuid4(),
        title="Buffer overflow in parser",
    )
    inv = await clean_service.create_investigation(req, user_id="user-123")

    # CREATED -> INGESTING
    s1 = await clean_service.start_investigation(inv.id)
    assert s1.status == InvestigationStatus.INGESTING

    # INGESTING -> REPRODUCING
    s2 = await clean_service.transition_investigation(
        inv.id, InvestigationStatus.REPRODUCING
    )
    assert s2.status == InvestigationStatus.REPRODUCING

    # REPRODUCING -> INVESTIGATING
    s3 = await clean_service.transition_investigation(
        inv.id, InvestigationStatus.INVESTIGATING
    )
    assert s3.status == InvestigationStatus.INVESTIGATING

    # INVESTIGATING -> VERIFYING
    s4 = await clean_service.transition_investigation(
        inv.id, InvestigationStatus.VERIFYING
    )
    assert s4.status == InvestigationStatus.VERIFYING

    # VERIFYING -> COMPLETED
    s5 = await clean_service.transition_investigation(
        inv.id, InvestigationStatus.COMPLETED
    )
    assert s5.status == InvestigationStatus.COMPLETED

    # Verify event timeline
    events_resp = await clean_service.get_events(inv.id)
    assert events_resp.total == 6
    expected_statuses = [
        (None, InvestigationStatus.CREATED),
        (InvestigationStatus.CREATED, InvestigationStatus.INGESTING),
        (InvestigationStatus.INGESTING, InvestigationStatus.REPRODUCING),
        (InvestigationStatus.REPRODUCING, InvestigationStatus.INVESTIGATING),
        (InvestigationStatus.INVESTIGATING, InvestigationStatus.VERIFYING),
        (InvestigationStatus.VERIFYING, InvestigationStatus.COMPLETED),
    ]
    for i, (from_st, to_st) in enumerate(expected_statuses):
        assert events_resp.items[i].from_status == from_st
        assert events_resp.items[i].to_status == to_st

    # Attempting to start or transition completed investigation must fail
    with pytest.raises(InvestigationAlreadyTerminalError):
        await clean_service.start_investigation(inv.id)

    with pytest.raises(InvestigationAlreadyTerminalError):
        await clean_service.transition_investigation(
            inv.id, InvestigationStatus.CREATED
        )


@pytest.mark.asyncio
async def test_invalid_transition_rejected(clean_service: InvestigationService):
    req = InvestigationCreate(
        repository_id=uuid4(),
        title="Invalid skip transition test",
    )
    inv = await clean_service.create_investigation(req, user_id="user-123")

    # CREATED -> COMPLETED is illegal
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        await clean_service.transition_investigation(
            inv.id, InvestigationStatus.COMPLETED
        )
    assert exc_info.value.code == "INVALID_STATE_TRANSITION"


@pytest.mark.asyncio
async def test_nonexistent_investigation_raises_404(
    clean_service: InvestigationService,
):
    random_id = uuid4()
    with pytest.raises(InvestigationNotFoundError) as exc_info:
        await clean_service.get_investigation(random_id)
    assert exc_info.value.code == "INVESTIGATION_NOT_FOUND"
    assert exc_info.value.status_code == 404

    with pytest.raises(InvestigationNotFoundError):
        await clean_service.get_events(random_id)
