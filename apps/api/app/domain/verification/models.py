"""Verification Domain Models"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    command: str = ""


class VerificationEvidence(BaseModel):
    investigation_id: UUID
    reproduction_run: ExecutionResult
    regression_test_run: ExecutionResult
    post_patch_test_run: ExecutionResult
    verified: bool = Field(..., description="True if patch passed all deterministic criteria")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
