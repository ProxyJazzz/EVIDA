"""Investigation Domain Models

Defines canonical investigation lifecycle states, hypotheses, events, and entity records.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class InvestigationStatus(StrEnum):
    """Canonical investigation lifecycle state machine statuses."""

    CREATED = "CREATED"
    INGESTING = "INGESTING"
    REPRODUCING = "REPRODUCING"
    INVESTIGATING = "INVESTIGATING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    # Backward compatibility for Phase 0 fixtures/models
    PENDING = "PENDING"
    HYPOTHESIZING = "HYPOTHESIZING"
    PATCHING = "PATCHING"
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class EventType(StrEnum):
    """Investigation lifecycle audit event types."""

    INVESTIGATION_CREATED = "INVESTIGATION_CREATED"
    INVESTIGATION_STARTED = "INVESTIGATION_STARTED"
    STATE_TRANSITIONED = "STATE_TRANSITIONED"
    INVESTIGATION_COMPLETED = "INVESTIGATION_COMPLETED"
    INVESTIGATION_FAILED = "INVESTIGATION_FAILED"
    INVESTIGATION_HYPOTHESIS_RECORDED = "INVESTIGATION_HYPOTHESIS_RECORDED"


class RootCauseCandidate(BaseModel):
    """Location and causal explanation of a suspected software defect."""

    file: str = Field(..., description="File path relative to repository root")
    symbol: str | None = Field(default=None, description="Function, method, or class name")
    line: int | None = Field(default=None, description="Line number where defect originates")
    description: str = Field(..., description="Causal explanation of the flaw")


class InvestigationHypothesis(BaseModel):
    """Structured causal hypothesis produced by the AI investigation engine."""

    hypothesis: str = Field(..., min_length=1, description="Core causal explanation of the failure")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence score (0.0 to 1.0)"
    )
    root_cause: RootCauseCandidate = Field(..., description="Structured root cause candidate")
    affected_files: list[str] = Field(default_factory=list, description="Target affected files")
    evidence: list[str] = Field(
        default_factory=list, description="Concrete observations grounding the hypothesis"
    )
    recommended_next_action: str = Field(
        default="generate_regression_test", description="Recommended next action"
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_phase0_compat(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map Phase 0 summary -> hypothesis
            if "hypothesis" not in data and "summary" in data:
                data["hypothesis"] = data["summary"]
            # Map Phase 0 string root_cause -> RootCauseCandidate
            if isinstance(data.get("root_cause"), str):
                data["root_cause"] = {
                    "file": "unknown",
                    "description": data["root_cause"],
                }
            # Map Phase 0 reproduction_strategy -> recommended_next_action
            if "recommended_next_action" not in data and "reproduction_strategy" in data:
                data["recommended_next_action"] = data["reproduction_strategy"]
        return data

    # Backward compatibility properties for Phase 0 code/tests
    @property
    def summary(self) -> str:
        return self.hypothesis

    @property
    def reproduction_strategy(self) -> str:
        return self.recommended_next_action


class InvestigationHypothesisRecord(BaseModel):
    """Persisted database record of an AI investigation hypothesis."""

    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    reproduction_run_id: UUID
    model: str
    provider: str
    hypothesis: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    root_cause: RootCauseCandidate
    affected_files: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    recommended_next_action: str = "generate_regression_test"
    raw_response: dict[str, Any] | None = None
    prompt_version: str = "evida-investigation-v1"
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InvestigationEvent(BaseModel):
    """Audit log entry for an investigation state transition or lifecycle milestone."""

    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    event_type: str = EventType.INVESTIGATION_CREATED
    from_status: InvestigationStatus | None = None
    to_status: InvestigationStatus
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Investigation(BaseModel):
    """Core domain entity for an EVIDA software repair investigation."""

    id: UUID = Field(default_factory=uuid4)
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

    # Backward compatibility property for Phase 0
    @property
    def issue_title(self) -> str:
        return self.title

    @property
    def issue_description(self) -> str | None:
        return self.bug_description
