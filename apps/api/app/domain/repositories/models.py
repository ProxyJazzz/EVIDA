"""Repository and Reproduction Domain Models

Defines repository archives, statuses, reproduction runs, and execution telemetry.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RepositoryStatus(StrEnum):
    """Lifecycle status of a repository archive."""

    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    EXTRACTING = "EXTRACTING"
    READY = "READY"
    FAILED = "FAILED"


class ReproductionStatus(StrEnum):
    """Reproduction execution verdict / status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    REPRODUCED = "REPRODUCED"
    NOT_REPRODUCED = "NOT_REPRODUCED"
    TIMEOUT = "TIMEOUT"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    POLICY_BLOCKED = "POLICY_BLOCKED"


class Repository(BaseModel):
    """Registered repository archive attached to an investigation."""

    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID | None = None
    project_id: UUID | None = None
    name: str
    storage_path: str = ""
    archive_size_bytes: int = 0
    archive_sha256: str = ""
    status: RepositoryStatus = RepositoryStatus.UPLOADED
    remote_url: str | None = None
    default_branch: str = "main"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RepositoryResponse(BaseModel):
    """API response contract for repository metadata."""

    id: UUID
    investigation_id: UUID | None = None
    name: str
    archive_size_bytes: int
    archive_sha256: str
    status: RepositoryStatus
    created_at: datetime
    updated_at: datetime


class ReproductionRun(BaseModel):
    """Deterministic record of an isolated sandbox reproduction execution."""

    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    repository_id: UUID
    command: str
    status: ReproductionStatus = ReproductionStatus.PENDING
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: int | None = None
    timed_out: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class ReproductionRunResponse(BaseModel):
    """API response contract for reproduction run evidence."""

    id: UUID
    investigation_id: UUID
    repository_id: UUID
    command: str
    status: ReproductionStatus
    exit_code: int | None = None
    stdout: str
    stderr: str
    duration_ms: int | None = None
    timed_out: bool = False
    created_at: datetime
    completed_at: datetime | None = None


class ReproductionRequest(BaseModel):
    """Input payload to initiate failure reproduction."""

    command: str = Field(
        default="pytest",
        min_length=1,
        max_length=500,
        description="Reproduction command to execute in sandbox",
    )


# Backward compatibility with Phase 0
class RepositoryCreate(BaseModel):
    project_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    remote_url: str | None = None
    default_branch: str = "main"


class RepositoryRead(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    name: str
    remote_url: str | None = None
    default_branch: str = "main"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
