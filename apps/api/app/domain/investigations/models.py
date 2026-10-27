"""Investigation Domain Models

Defines canonical investigation lifecycle states, hypotheses, events, and entity records.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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


class InvestigationHypothesis(BaseModel):
    summary: str = Field(..., description="High-level summary of the bug root cause")
    root_cause: str = Field(..., description="Technical explanation of the defect")
    affected_files: list[str] = Field(default_factory=list, description="Target source files")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    reproduction_strategy: str = Field(..., description="Proposed approach for reproduction")


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
