"""Investigation Domain Models

Defines investigation lifecycle states, hypotheses, and response entities.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class InvestigationStatus(StrEnum):
    PENDING = "PENDING"
    REPRODUCING = "REPRODUCING"
    INVESTIGATING = "INVESTIGATING"
    HYPOTHESIZING = "HYPOTHESIZING"
    PATCHING = "PATCHING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    FAILED = "FAILED"


class InvestigationHypothesis(BaseModel):
    summary: str = Field(..., description="High-level summary of the bug root cause")
    root_cause: str = Field(..., description="Technical explanation of the defect")
    affected_files: list[str] = Field(default_factory=list, description="Target source files")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    reproduction_strategy: str = Field(..., description="Proposed approach for reproduction")


class InvestigationCreate(BaseModel):
    repository_id: UUID
    issue_title: str = Field(..., min_length=3, max_length=255)
    issue_description: str | None = None


class InvestigationRead(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    repository_id: UUID
    issue_title: str
    issue_description: str | None = None
    status: InvestigationStatus = InvestigationStatus.PENDING
    hypothesis: InvestigationHypothesis | None = None
    regression_test_code: str | None = None
    candidate_patch: str | None = None
    verification_evidence: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InvestigationListResponse(BaseModel):
    items: list[InvestigationRead]
    total: int
