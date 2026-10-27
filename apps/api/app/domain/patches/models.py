"""Patch Domain Models"""

from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CandidatePatch(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    diff_content: str = Field(..., description="Unified diff string")
    explanation: str = Field(..., description="Explanation of changes")
    affected_files: list[str] = Field(default_factory=list)
