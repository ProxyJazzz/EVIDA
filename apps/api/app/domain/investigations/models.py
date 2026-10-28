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
    REGRESSION_TEST_GENERATED = "REGRESSION_TEST_GENERATED"
    REGRESSION_TEST_VERIFICATION_STARTED = "REGRESSION_TEST_VERIFICATION_STARTED"
    REGRESSION_TEST_VERIFICATION_COMPLETED = "REGRESSION_TEST_VERIFICATION_COMPLETED"
    REGRESSION_TEST_REJECTED = "REGRESSION_TEST_REJECTED"
    REGRESSION_TEST_PROVEN = "REGRESSION_TEST_PROVEN"
    PATCH_GENERATION_STARTED = "PATCH_GENERATION_STARTED"
    PATCH_GENERATED = "PATCH_GENERATED"
    PATCH_VALIDATED = "PATCH_VALIDATED"
    PATCH_REJECTED = "PATCH_REJECTED"

    # Phase 6: Deterministic Patch Verification & Double Validation Events
    PATCH_VERIFICATION_STARTED = "PATCH_VERIFICATION_STARTED"
    PATCH_APPLICATION_STARTED = "PATCH_APPLICATION_STARTED"
    PATCH_APPLICATION_COMPLETED = "PATCH_APPLICATION_COMPLETED"
    PATCH_APPLICATION_FAILED = "PATCH_APPLICATION_FAILED"
    REGRESSION_VERIFICATION_PASSED = "REGRESSION_VERIFICATION_PASSED"
    REGRESSION_VERIFICATION_FAILED = "REGRESSION_VERIFICATION_FAILED"
    BASELINE_VERIFICATION_STARTED = "BASELINE_VERIFICATION_STARTED"
    BASELINE_VERIFICATION_COMPLETED = "BASELINE_VERIFICATION_COMPLETED"
    BASELINE_VERIFICATION_PASSED = "BASELINE_VERIFICATION_PASSED"
    BASELINE_VERIFICATION_FAILED = "BASELINE_VERIFICATION_FAILED"
    PATCH_VERIFIED = "PATCH_VERIFIED"
    PATCH_UNVERIFIED = "PATCH_UNVERIFIED"
    SOURCE_INTEGRITY_CHECKED = "SOURCE_INTEGRITY_CHECKED"
    SOURCE_INTEGRITY_VIOLATION = "SOURCE_INTEGRITY_VIOLATION"


class RegressionTestGenerationStatus(StrEnum):
    """Status of AI regression test code generation."""

    GENERATED = "GENERATED"
    REJECTED = "REJECTED"


class RegressionVerificationStatus(StrEnum):
    """Objective deterministic execution verdict of the regression test."""

    PENDING = "PENDING"
    REGRESSION_PROVEN = "REGRESSION_PROVEN"
    TEST_REJECTED = "TEST_REJECTED"
    TIMEOUT = "TIMEOUT"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    POLICY_BLOCKED = "POLICY_BLOCKED"


class RegressionFailureClassification(StrEnum):
    """Detailed failure classification distinguishing real assertion failure from execution flaws."""

    ASSERTION_FAILURE = "ASSERTION_FAILURE"
    TEST_EXECUTION_ERROR = "TEST_EXECUTION_ERROR"
    PASSING = "PASSING"
    TIMEOUT = "TIMEOUT"
    POLICY_BLOCKED = "POLICY_BLOCKED"


class RegressionTestProposal(BaseModel):
    """Strict structured response expected from the AI regression test generation engine."""

    test_path: str = Field(
        ...,
        description="Target relative test path inside repository, e.g. tests/test_regression.py",
    )
    framework: str = Field(default="pytest", description="Testing framework used")
    language: str = Field(default="python", description="Language of the regression test")
    description: str = Field(..., description="Explanation of what the regression test verifies")
    test_content: str = Field(..., min_length=1, description="Raw executable test code")
    target_symbol: str = Field(..., description="Target function, method, or class being tested")
    target_file: str = Field(..., description="Target source file where the defect originates")
    expected_failure_reason: str = Field(
        ..., description="Why the test is expected to fail on the buggy codebase"
    )


class InvestigationRegressionTestRecord(BaseModel):
    """Persisted database record of an AI-generated regression test."""

    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    hypothesis_id: UUID
    test_path: str
    test_content: str
    framework: str = "pytest"
    language: str = "python"
    description: str
    target_symbol: str | None = None
    target_file: str | None = None
    expected_failure_reason: str | None = None
    status: RegressionTestGenerationStatus = RegressionTestGenerationStatus.GENERATED
    verification_status: RegressionVerificationStatus | None = RegressionVerificationStatus.PENDING
    verification_run_id: UUID | None = None
    model: str | None = None
    provider: str | None = None
    prompt_version: str = "evida-regression-test-v1"
    raw_response: dict[str, Any] | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    verified_at: datetime | None = None


class RegressionVerificationRun(BaseModel):
    """Persisted record of an isolated sandbox verification run for a regression test."""

    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    regression_test_id: UUID
    command: str
    status: RegressionVerificationStatus
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: int | None = None
    timed_out: bool = False
    failure_classification: RegressionFailureClassification | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


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
