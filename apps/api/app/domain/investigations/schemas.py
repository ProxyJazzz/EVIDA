"""Investigation Request & Response Schemas (Pydantic v2)"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from app.domain.investigations.models import (
    EventType,
    InvestigationHypothesis,
    InvestigationStatus,
    RootCauseCandidate,
)


class InvestigationCreate(BaseModel):
    """Payload for creating a new investigation."""

    project_id: UUID | None = Field(default=None, description="Optional parent project identifier")
    repository_id: UUID = Field(..., description="Target repository UUID")
    title: str | None = Field(default=None, min_length=1, max_length=255)
    bug_description: str | None = Field(default=None, description="Detailed problem description")

    # Backward compatibility aliases for Phase 0
    issue_title: str | None = Field(default=None, min_length=1, max_length=255)
    issue_description: str | None = None

    @model_validator(mode="before")
    @classmethod
    def resolve_title_and_description(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Consolidate title / issue_title
            title = data.get("title") or data.get("issue_title")
            if not title or not str(title).strip():
                raise ValueError("Investigation title is required.")
            data["title"] = str(title).strip()

            # Consolidate bug_description / issue_description
            desc = data.get("bug_description") or data.get("issue_description")
            data["bug_description"] = desc
        return data


class InvestigationResponse(BaseModel):
    """Public representation of an investigation."""

    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID | None = None
    project_id: UUID | None = None
    repository_id: UUID
    title: str
    bug_description: str | None = None
    status: InvestigationStatus = InvestigationStatus.CREATED
    hypothesis: InvestigationHypothesis | None = None
    regression_test_code: str | None = None
    candidate_patch: str | None = None
    verification_evidence: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def sync_investigation_id(self) -> InvestigationResponse:
        if self.investigation_id is None:
            self.investigation_id = self.id
        return self

    # Backward compatibility properties for Phase 0 tests
    @property
    def issue_title(self) -> str:
        return self.title

    @property
    def issue_description(self) -> str | None:
        return self.bug_description


# Alias for backward compatibility
InvestigationRead = InvestigationResponse


class InvestigationListResponse(BaseModel):
    items: list[InvestigationResponse]
    total: int


class InvestigationEventResponse(BaseModel):
    """Public representation of an investigation timeline event."""

    id: UUID
    investigation_id: UUID
    event_type: str = EventType.INVESTIGATION_CREATED
    from_status: InvestigationStatus | None = None
    to_status: InvestigationStatus
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class InvestigationEventsResponse(BaseModel):
    items: list[InvestigationEventResponse]
    total: int


class StateTransitionRequest(BaseModel):
    """Explicit state transition request for testing and operator overrides."""

    target_status: InvestigationStatus
    metadata: dict[str, Any] = Field(default_factory=dict)


class InvestigationHypothesisResponse(BaseModel):
    """Public API response contract for an AI investigation hypothesis."""

    id: UUID
    investigation_id: UUID
    reproduction_run_id: UUID
    model: str
    provider: str
    prompt_version: str
    hypothesis: str
    confidence: float
    root_cause: RootCauseCandidate
    affected_files: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    recommended_next_action: str = "generate_regression_test"
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    created_at: datetime


class RegressionVerificationResponse(BaseModel):
    """Public API response representing deterministic sandbox verification of a regression test."""

    id: UUID
    command: str
    status: str
    exit_code: int | None = None
    duration_ms: int | None = None
    failure_classification: str | None = None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    created_at: datetime
    completed_at: datetime | None = None


class RegressionTestResponse(BaseModel):
    """Public API response contract for an AI-generated regression test and its verification result."""

    id: UUID
    investigation_id: UUID
    hypothesis_id: UUID
    test_path: str
    framework: str = "pytest"
    language: str = "python"
    description: str
    test_content: str
    target_symbol: str | None = None
    target_file: str | None = None
    expected_failure_reason: str | None = None
    generation_status: str
    verification_status: str | None = None
    model: str | None = None
    provider: str | None = None
    prompt_version: str = "evida-regression-test-v1"
    verification: RegressionVerificationResponse | None = None
    created_at: datetime
    verified_at: datetime | None = None


class PatchCandidateResponse(BaseModel):
    """Public API response contract for an AI-generated patch candidate (Phase 5)."""

    id: UUID
    investigation_id: UUID
    hypothesis_id: UUID
    regression_test_id: UUID
    status: str
    description: str
    patch_format: str = "unified_diff"
    patch_content: str
    changed_files: list[str] = Field(default_factory=list)
    change_summary: list[dict[str, Any]] = Field(default_factory=list)
    reasoning: str | None = None
    validation_result: str | None = None
    validation_errors: list[str] = Field(default_factory=list)
    verification_status: str = "NOT_VERIFIED"
    model: str | None = None
    provider: str | None = None
    prompt_version: str = "evida-patch-generation-v1"
    created_at: datetime
    validated_at: datetime | None = None
