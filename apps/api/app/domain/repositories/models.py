"""Repository Domain Models"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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
