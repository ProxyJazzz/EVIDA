"""Worker Job Definitions"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class JobType(StrEnum):
    REPRODUCE_FAILURE = "REPRODUCE_FAILURE"
    RUN_REGRESSION_TEST = "RUN_REGRESSION_TEST"
    APPLY_AND_VERIFY_PATCH = "APPLY_AND_VERIFY_PATCH"


class SandboxJob(BaseModel):
    investigation_id: UUID
    job_type: JobType
    command: str = Field(..., description="Command to execute in sandbox")
    timeout_seconds: float = 60.0
