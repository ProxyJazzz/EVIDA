"""Domain Models and Schemas for Phase 6: Deterministic Patch Verification & Double Validation

Defines the contracts for patch application, regression verification, baseline verification,
and deterministic verdict classifications.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PatchVerificationStatus(StrEnum):
    """Lifecycle progress states of a patch verification run."""

    PENDING = "PENDING"
    PATCH_APPLIED = "PATCH_APPLIED"
    REGRESSION_RUNNING = "REGRESSION_RUNNING"
    REGRESSION_PASSED = "REGRESSION_PASSED"
    BASELINE_RUNNING = "BASELINE_RUNNING"
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    FAILED = "FAILED"


class PatchVerificationVerdict(StrEnum):
    """Objective deterministic verdict for patch verification."""

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class VerificationFailureClassification(StrEnum):
    """Deterministic failure taxonomy for unverified patches."""

    PATCH_APPLICATION_FAILED = "PATCH_APPLICATION_FAILED"
    PATCH_APPLICATION_TIMEOUT = "PATCH_APPLICATION_TIMEOUT"
    PATCH_APPLICATION_POLICY_BLOCKED = "PATCH_APPLICATION_POLICY_BLOCKED"
    REGRESSION_STILL_FAILING = "REGRESSION_STILL_FAILING"
    REGRESSION_EXECUTION_ERROR = "REGRESSION_EXECUTION_ERROR"
    REGRESSION_TIMEOUT = "REGRESSION_TIMEOUT"
    REGRESSION_POLICY_BLOCKED = "REGRESSION_POLICY_BLOCKED"
    BASELINE_TEST_FAILURE = "BASELINE_TEST_FAILURE"
    BASELINE_EXECUTION_ERROR = "BASELINE_EXECUTION_ERROR"
    BASELINE_TIMEOUT = "BASELINE_TIMEOUT"
    BASELINE_POLICY_BLOCKED = "BASELINE_POLICY_BLOCKED"
    SOURCE_INTEGRITY_VIOLATION = "SOURCE_INTEGRITY_VIOLATION"
    UNEXPECTED_WORKSPACE_CHANGE = "UNEXPECTED_WORKSPACE_CHANGE"


@dataclass
class ExecutionResult:
    """Sandbox execution result for worker jobs."""

    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    command: list[str] | str = ""


@dataclass
class PatchApplicationResult:
    """Detailed result of applying a unified diff to a fresh workspace."""

    status: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    modified_files: list[str] = field(default_factory=list)
    created_files: list[str] = field(default_factory=list)
    deleted_files: list[str] = field(default_factory=list)


@dataclass
class VerificationTestResult:
    """Result of running a test suite (regression or baseline) in sandbox."""

    status: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float


@dataclass
class PatchVerificationRun:
    """Internal persistence record representing a deterministic patch verification run."""

    id: UUID
    investigation_id: UUID
    patch_candidate_id: UUID
    regression_test_id: UUID
    status: PatchVerificationStatus
    patch_sha256: str
    repository_sha256: str
    patch_application_status: str
    patch_application_exit_code: int
    patch_application_stdout: str
    patch_application_stderr: str
    regression_status: str
    regression_exit_code: int | None
    regression_stdout: str
    regression_stderr: str
    regression_duration_ms: int
    baseline_status: str
    baseline_command: str
    baseline_exit_code: int | None
    baseline_stdout: str
    baseline_stderr: str
    baseline_duration_ms: int
    verdict: PatchVerificationVerdict
    failure_classification: VerificationFailureClassification | None = None
    workspace_file_manifest: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class PatchApplicationResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    modified_files: list[str] = Field(default_factory=list)
    created_files: list[str] = Field(default_factory=list)
    deleted_files: list[str] = Field(default_factory=list)


class VerificationTestResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float


class PatchVerificationResponse(BaseModel):
    """Public API response schema for Phase 6 patch verification."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    investigation_id: UUID
    patch_candidate_id: UUID
    regression_test_id: UUID
    status: PatchVerificationStatus
    verdict: PatchVerificationVerdict
    failure_classification: VerificationFailureClassification | str | None = None
    patch_sha256: str
    repository_sha256: str
    patch_application: PatchApplicationResponse
    regression_execution: VerificationTestResponse
    baseline_execution: VerificationTestResponse
    workspace_file_manifest: dict[str, str] = Field(default_factory=dict)
    source_integrity_verified: bool
    created_at: datetime
    completed_at: datetime
