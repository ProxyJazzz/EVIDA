"""Investigation Routes (Phase 1 Lifecycle Implementation)"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status

from app.api.dependencies import (
    AIInvestigationServiceDep,
    InvestigationServiceDep,
    RegressionServiceDep,
    ReproductionServiceDep,
    UserIdDep,
)
from app.domain.investigations.schemas import (
    InvestigationCreate,
    InvestigationEventsResponse,
    InvestigationHypothesisResponse,
    InvestigationListResponse,
    InvestigationResponse,
    RegressionTestResponse,
)
from app.domain.repositories.models import (
    RepositoryResponse,
    ReproductionRequest,
    ReproductionRunResponse,
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


@router.post(
    "/{investigation_id}/repository",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest repository archive for investigation",
)
async def upload_repository(
    investigation_id: UUID,
    service: ReproductionServiceDep,
    file: Annotated[UploadFile, File()],
) -> RepositoryResponse:
    """Securely upload and validate a repository ZIP archive, advancing state to INGESTING."""
    content = await file.read()
    filename = file.filename or "repository.zip"
    return await service.ingest_repository_archive(
        investigation_id=investigation_id,
        filename=filename,
        content=content,
    )


@router.get(
    "/{investigation_id}/repository",
    response_model=RepositoryResponse,
    summary="Get repository metadata for investigation",
)
async def get_repository(
    investigation_id: UUID,
    service: ReproductionServiceDep,
) -> RepositoryResponse:
    """Retrieve metadata and security verification status for the attached repository archive."""
    return await service.get_repository(investigation_id)


@router.post(
    "/{investigation_id}/reproduce",
    response_model=ReproductionRunResponse,
    summary="Execute failure reproduction in isolated sandbox",
)
async def reproduce_failure(
    investigation_id: UUID,
    payload: ReproductionRequest,
    service: ReproductionServiceDep,
) -> ReproductionRunResponse:
    """Safely execute the reproduction command within an ephemeral workspace and capture evidence."""
    return await service.reproduce_failure(
        investigation_id=investigation_id,
        command=payload.command,
    )


@router.get(
    "/{investigation_id}/reproduction",
    response_model=ReproductionRunResponse,
    summary="Get latest reproduction run result",
)
async def get_reproduction(
    investigation_id: UUID,
    service: ReproductionServiceDep,
) -> ReproductionRunResponse:
    """Retrieve the latest objective reproduction run execution evidence and verdict."""
    return await service.get_reproduction(investigation_id)


@router.post(
    "/{investigation_id}/investigate",
    response_model=InvestigationHypothesisResponse,
    summary="Start AI investigation and formulate causal hypothesis",
)
async def investigate_failure(
    investigation_id: UUID,
    service: AIInvestigationServiceDep,
) -> InvestigationHypothesisResponse:
    """Analyze deterministic reproduction evidence and repository context to synthesize a causal hypothesis."""
    return await service.investigate_failure(investigation_id)


@router.get(
    "/{investigation_id}/hypothesis",
    response_model=InvestigationHypothesisResponse,
    summary="Get latest AI investigation hypothesis",
)
async def get_hypothesis(
    investigation_id: UUID,
    service: AIInvestigationServiceDep,
) -> InvestigationHypothesisResponse:
    """Retrieve the latest structured causal hypothesis generated by the AI investigation engine."""
    return await service.get_hypothesis(investigation_id)


@router.post(
    "/{investigation_id}/regression-test",
    response_model=RegressionTestResponse,
    summary="Generate and deterministically verify regression test",
)
async def generate_regression_test(
    investigation_id: UUID,
    service: RegressionServiceDep,
) -> RegressionTestResponse:
    """Transform causal hypothesis into a standalone regression test and execute against unpatched codebase."""
    return await service.generate_and_verify_regression_test(investigation_id)


@router.get(
    "/{investigation_id}/regression-test",
    response_model=RegressionTestResponse,
    summary="Get latest generated regression test and verification result",
)
async def get_regression_test(
    investigation_id: UUID,
    service: RegressionServiceDep,
) -> RegressionTestResponse:
    """Retrieve the latest generated regression test and deterministic verification result."""
    result = await service.get_regression_test(investigation_id)
    if not result:
        from app.domain.investigations.state_machine import LifecycleException

        raise LifecycleException(
            f"No regression test found for investigation '{investigation_id}'.",
            code="REGRESSION_TEST_NOT_FOUND",
            status_code=404,
        )
    return result
