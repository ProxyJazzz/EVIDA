"""Investigation Routes (Phase 1 Lifecycle Implementation)"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.api.dependencies import InvestigationServiceDep, UserIdDep
from app.domain.investigations.schemas import (
    InvestigationCreate,
    InvestigationEventsResponse,
    InvestigationListResponse,
    InvestigationResponse,
)

router = APIRouter(prefix="/investigations", tags=["Investigations"])


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new repair investigation",
)
async def create_investigation(
    payload: InvestigationCreate,
    service: InvestigationServiceDep,
    user_id: UserIdDep,
) -> InvestigationResponse:
    """Create a new software repair investigation with initial status CREATED."""
    return await service.create_investigation(payload, user_id=user_id)


@router.get(
    "",
    response_model=InvestigationListResponse,
    summary="List investigations",
)
async def list_investigations(
    service: InvestigationServiceDep,
    user_id: UserIdDep,
) -> InvestigationListResponse:
    """List all repair investigations for the authenticated user/tenant."""
    return await service.list_investigations(user_id=user_id)


@router.get(
    "/{investigation_id}",
    response_model=InvestigationResponse,
    summary="Get investigation by ID",
)
async def get_investigation(
    investigation_id: UUID,
    service: InvestigationServiceDep,
) -> InvestigationResponse:
    """Retrieve details and status for a specific investigation."""
    return await service.get_investigation(investigation_id)


@router.post(
    "/{investigation_id}/start",
    response_model=InvestigationResponse,
    summary="Start investigation lifecycle",
)
async def start_investigation(
    investigation_id: UUID,
    service: InvestigationServiceDep,
) -> InvestigationResponse:
    """Start an investigation by transitioning from CREATED to INGESTING.

    Idempotent: If already in INGESTING or subsequent active state, returns
    the current investigation state without restarting or corrupting lifecycle.
    """
    return await service.start_investigation(investigation_id)


@router.get(
    "/{investigation_id}/events",
    response_model=InvestigationEventsResponse,
    summary="Get investigation chronological event timeline",
)
async def get_investigation_events(
    investigation_id: UUID,
    service: InvestigationServiceDep,
) -> InvestigationEventsResponse:
    """Retrieve chronologically ordered lifecycle events and audit trail."""
    return await service.get_events(investigation_id)
