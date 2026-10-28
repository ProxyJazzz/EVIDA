"""Patch Domain Models (Phase 5)

Defines patch candidate statuses, proposal schemas, entity records, and validation classifications.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PatchCandidateStatus(StrEnum):
    """Lifecycle status of an AI-generated patch candidate."""

    GENERATED = "GENERATED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class PatchValidationClassification(StrEnum):
    """Deterministic structural, scope, and security validation classification."""

    VALID = "VALID"
    INVALID_FORMAT = "INVALID_FORMAT"
    PATH_VIOLATION = "PATH_VIOLATION"
    SENSITIVE_FILE_MODIFICATION = "SENSITIVE_FILE_MODIFICATION"
    TEST_MODIFICATION = "TEST_MODIFICATION"
    OUT_OF_SCOPE_CHANGE = "OUT_OF_SCOPE_CHANGE"
    PATCH_TOO_LARGE = "PATCH_TOO_LARGE"
    MALFORMED_DIFF = "MALFORMED_DIFF"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"


class ChangeSummaryItem(BaseModel):
    """File-level explanation of change within candidate patch."""

    file: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class PatchProposal(BaseModel):
    """Strict structured response expected from AI patch generation."""

    description: str = Field(..., min_length=1, max_length=2000)
    patch_format: Literal["unified_diff"] = "unified_diff"
    patch_content: str = Field(..., min_length=1)
    changed_files: list[str] = Field(..., min_length=1)
    change_summary: list[ChangeSummaryItem] = Field(default_factory=list)
    reasoning: str = Field(..., min_length=1, max_length=4000)


class PatchValidationResult(BaseModel):
    """Result of deterministic validation of a patch candidate."""

    is_valid: bool
    classification: PatchValidationClassification
    errors: list[str] = Field(default_factory=list)
    parsed_files: list[str] = Field(default_factory=list)
    hunk_count: int = 0


class PatchCandidateRecord(BaseModel):
    """Persistent entity record representing a generated and validated patch candidate."""

    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    hypothesis_id: UUID
    regression_test_id: UUID
    status: PatchCandidateStatus = PatchCandidateStatus.GENERATED
    description: str
    patch_format: str = "unified_diff"
    patch_content: str
    changed_files: list[str] = Field(default_factory=list)
    change_summary: list[dict[str, Any]] = Field(default_factory=list)
    reasoning: str | None = None
    validation_result: PatchValidationClassification | str | None = None
    validation_errors: list[str] = Field(default_factory=list)
    model: str | None = None
    provider: str | None = None
    prompt_version: str = "evida-patch-generation-v1"
    raw_response: dict[str, Any] | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    validated_at: datetime | None = None
