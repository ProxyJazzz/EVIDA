"""Investigation Routes (Phase 1 Lifecycle Implementation)"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Response, UploadFile, status

from app.api.dependencies import (
    AIInvestigationServiceDep,
    EvidenceServiceDep,
    InvestigationServiceDep,
    PatchServiceDep,
    PatchVerificationServiceDep,
    RegressionServiceDep,
    ReproductionServiceDep,
    UserIdDep,
)
from app.domain.evidence.models import EvidenceBundle, EvidenceHashResponse, EvidenceItem
from app.domain.investigations.schemas import (
    InvestigationCreate,
    InvestigationEventsResponse,
    InvestigationHypothesisResponse,
    InvestigationListResponse,
    InvestigationResponse,
    PatchCandidateResponse,
    RegressionTestResponse,
)
from app.domain.repositories.models import (
    RepositoryResponse,
    ReproductionRequest,
    ReproductionRunResponse,
)
from app.domain.verification.models import PatchVerificationResponse

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
    user_id: UserIdDep,
) -> InvestigationResponse:
    """Retrieve details and status for a specific investigation."""
    return await service.get_investigation(investigation_id, user_id=user_id)


@router.post(
    "/{investigation_id}/start",
    response_model=InvestigationResponse,
    summary="Start investigation lifecycle",
)
async def start_investigation(
    investigation_id: UUID,
    service: InvestigationServiceDep,
    user_id: UserIdDep,
) -> InvestigationResponse:
    """Start an investigation by transitioning from CREATED to INGESTING.

    Idempotent: If already in INGESTING or subsequent active state, returns
    the current investigation state without restarting or corrupting lifecycle.
    """
    return await service.start_investigation(investigation_id, user_id=user_id)


@router.get(
    "/{investigation_id}/events",
    response_model=InvestigationEventsResponse,
    summary="Get investigation chronological event timeline",
)
async def get_investigation_events(
    investigation_id: UUID,
    service: InvestigationServiceDep,
    user_id: UserIdDep,
) -> InvestigationEventsResponse:
    """Retrieve chronologically ordered lifecycle events and audit trail."""
    return await service.get_events(investigation_id, user_id=user_id)


@router.post(
    "/{investigation_id}/repository",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest repository archive for investigation",
)
async def upload_repository(
    investigation_id: UUID,
    service: ReproductionServiceDep,
    user_id: UserIdDep,
    file: Annotated[UploadFile, File()],
) -> RepositoryResponse:
    """Securely upload and validate a repository ZIP archive, advancing state to INGESTING."""
    content = await file.read()
    filename = file.filename or "repository.zip"
    return await service.ingest_repository_archive(
        investigation_id=investigation_id,
        filename=filename,
        content=content,
        user_id=user_id,
    )


@router.get(
    "/{investigation_id}/repository",
    response_model=RepositoryResponse,
    summary="Get repository metadata for investigation",
)
async def get_repository(
    investigation_id: UUID,
    service: ReproductionServiceDep,
    user_id: UserIdDep,
) -> RepositoryResponse:
    """Retrieve metadata and security verification status for the attached repository archive."""
    return await service.get_repository(investigation_id, user_id=user_id)


@router.post(
    "/{investigation_id}/reproduce",
    response_model=ReproductionRunResponse,
    summary="Execute failure reproduction in isolated sandbox",
)
async def reproduce_failure(
    investigation_id: UUID,
    payload: ReproductionRequest,
    service: ReproductionServiceDep,
    user_id: UserIdDep,
) -> ReproductionRunResponse:
    """Safely execute the reproduction command within an ephemeral workspace and capture evidence."""
    return await service.reproduce_failure(
        investigation_id=investigation_id,
        command=payload.command,
        user_id=user_id,
    )


@router.get(
    "/{investigation_id}/reproduction",
    response_model=ReproductionRunResponse,
    summary="Get latest reproduction run result",
)
async def get_reproduction(
    investigation_id: UUID,
    service: ReproductionServiceDep,
    user_id: UserIdDep,
) -> ReproductionRunResponse:
    """Retrieve the latest objective reproduction run execution evidence and verdict."""
    return await service.get_reproduction(investigation_id, user_id=user_id)


@router.post(
    "/{investigation_id}/investigate",
    response_model=InvestigationHypothesisResponse,
    summary="Start AI investigation and formulate causal hypothesis",
)
async def investigate_failure(
    investigation_id: UUID,
    service: AIInvestigationServiceDep,
    user_id: UserIdDep,
) -> InvestigationHypothesisResponse:
    """Analyze deterministic reproduction evidence and repository context to synthesize a causal hypothesis."""
    return await service.investigate_failure(investigation_id, user_id=user_id)


@router.get(
    "/{investigation_id}/hypothesis",
    response_model=InvestigationHypothesisResponse,
    summary="Get latest AI investigation hypothesis",
)
async def get_hypothesis(
    investigation_id: UUID,
    service: AIInvestigationServiceDep,
    user_id: UserIdDep,
) -> InvestigationHypothesisResponse:
    """Retrieve the latest structured causal hypothesis generated by the AI investigation engine."""
    return await service.get_hypothesis(investigation_id, user_id=user_id)


@router.post(
    "/{investigation_id}/regression-test",
    response_model=RegressionTestResponse,
    summary="Generate and deterministically verify regression test",
)
async def generate_regression_test(
    investigation_id: UUID,
    service: RegressionServiceDep,
    user_id: UserIdDep,
) -> RegressionTestResponse:
    """Transform causal hypothesis into a standalone regression test and execute against unpatched codebase."""
    return await service.generate_and_verify_regression_test(investigation_id, user_id=user_id)


@router.get(
    "/{investigation_id}/regression-test",
    response_model=RegressionTestResponse,
    summary="Get latest generated regression test and verification result",
)
async def get_regression_test(
    investigation_id: UUID,
    service: RegressionServiceDep,
    user_id: UserIdDep,
) -> RegressionTestResponse:
    """Retrieve the latest generated regression test and deterministic verification result."""
    result = await service.get_regression_test(investigation_id, user_id=user_id)
    if not result:
        from app.domain.investigations.state_machine import LifecycleException

        raise LifecycleException(
            f"No regression test found for investigation '{investigation_id}'.",
            code="REGRESSION_TEST_NOT_FOUND",
            status_code=404,
        )
    return result


@router.post(
    "/{investigation_id}/patch",
    response_model=PatchCandidateResponse,
    summary="Generate and validate candidate patch",
)
async def generate_patch(
    investigation_id: UUID,
    service: PatchServiceDep,
    user_id: UserIdDep,
) -> PatchCandidateResponse:
    """Synthesize a candidate unified diff patch based on proven regression evidence and validate safety."""
    return await service.generate_and_validate_patch(investigation_id, user_id=user_id)


@router.get(
    "/{investigation_id}/patch",
    response_model=PatchCandidateResponse,
    summary="Get latest candidate patch and validation result",
)
async def get_patch(
    investigation_id: UUID,
    service: PatchServiceDep,
    user_id: UserIdDep,
) -> PatchCandidateResponse:
    """Retrieve the latest synthesized candidate patch and its deterministic validation result."""
    return await service.get_patch_candidate(investigation_id, user_id=user_id)


@router.post(
    "/{investigation_id}/verify-patch",
    response_model=PatchVerificationResponse,
    summary="Execute deterministic double validation on candidate patch",
)
async def verify_patch(
    investigation_id: UUID,
    service: PatchVerificationServiceDep,
    user_id: UserIdDep,
) -> PatchVerificationResponse:
    """Execute candidate patch in an isolated ephemeral workspace with double validation (regression + baseline)."""
    return await service.verify_patch_candidate(investigation_id, user_id=user_id)


@router.get(
    "/{investigation_id}/verification",
    response_model=PatchVerificationResponse,
    summary="Get latest patch verification run and double validation evidence",
)
async def get_latest_verification(
    investigation_id: UUID,
    service: PatchVerificationServiceDep,
    user_id: UserIdDep,
) -> PatchVerificationResponse:
    """Retrieve the latest deterministic patch verification run and objective execution evidence."""
    return await service.get_latest_verification(investigation_id, user_id=user_id)


@router.get(
    "/{investigation_id}/verifications",
    response_model=list[PatchVerificationResponse],
    summary="List all patch verification runs for investigation",
)
async def list_verifications(
    investigation_id: UUID,
    service: PatchVerificationServiceDep,
    user_id: UserIdDep,
) -> list[PatchVerificationResponse]:
    """Retrieve historical verification runs for an investigation."""
    return await service.list_verifications(investigation_id, user_id=user_id)


# Phase 7: Evidence Bundle, Provenance & Audit System Endpoints


@router.get(
    "/{investigation_id}/evidence",
    response_model=EvidenceBundle,
    summary="Get complete cryptographically fingerprinted evidence bundle",
)
async def get_evidence_bundle(
    investigation_id: UUID,
    service: EvidenceServiceDep,
    user_id: UserIdDep,
) -> EvidenceBundle:
    """Retrieve the aggregate evidence bundle containing the complete proof chain and bundle SHA-256."""
    return await service.get_or_build_evidence_bundle(investigation_id, user_id=user_id)


@router.get(
    "/{investigation_id}/evidence/items",
    response_model=list[EvidenceItem],
    summary="List individual evidence items with explicit provenance",
)
async def list_evidence_items(
    investigation_id: UUID,
    service: EvidenceServiceDep,
    user_id: UserIdDep,
) -> list[EvidenceItem]:
    """Retrieve chronological individual evidence items with explicit AI vs deterministic provenance."""
    return await service.list_evidence_items(investigation_id, user_id=user_id)


@router.get(
    "/{investigation_id}/evidence/hash",
    response_model=EvidenceHashResponse,
    summary="Get compact bundle SHA-256 fingerprint",
)
async def get_bundle_hash(
    investigation_id: UUID,
    service: EvidenceServiceDep,
    user_id: UserIdDep,
) -> EvidenceHashResponse:
    """Retrieve the compact SHA-256 bundle hash for evidence chain verification."""
    return await service.get_bundle_hash(investigation_id, user_id=user_id)


@router.get(
    "/{investigation_id}/evidence/export",
    summary="Export machine-readable evidence bundle as JSON",
)
async def export_evidence_bundle(
    investigation_id: UUID,
    service: EvidenceServiceDep,
    user_id: UserIdDep,
) -> Response:
    """Export the complete evidence bundle formatted as canonical JSON with attachment header."""
    json_str = await service.export_bundle_json(investigation_id, user_id=user_id)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="evida-evidence-{investigation_id}.json"'
        },
    )
