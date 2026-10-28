"""Domain Models and Contracts for Phase 7: Evidence Bundle, Provenance & Audit System

Defines evidence provenance classes, evidence types, individual evidence items,
the immutable aggregate EvidenceBundle, and cryptographic content hashing.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class EvidenceProvenance(StrEnum):
    """Categorical source and trust boundary classification for an evidence item."""

    AI_PROPOSAL = "AI_PROPOSAL"
    DETERMINISTIC_EXECUTION = "DETERMINISTIC_EXECUTION"
    CRYPTOGRAPHIC_INTEGRITY = "CRYPTOGRAPHIC_INTEGRITY"
    SYSTEM_METADATA = "SYSTEM_METADATA"
    AUDIT_EVENT = "AUDIT_EVENT"


class EvidenceType(StrEnum):
    """Explicit taxonomy of evidence items forming the causal investigation chain."""

    INCIDENT = "INCIDENT"
    REPOSITORY = "REPOSITORY"
    REPRODUCTION = "REPRODUCTION"
    HYPOTHESIS = "HYPOTHESIS"
    REGRESSION_TEST = "REGRESSION_TEST"
    REGRESSION_PROOF = "REGRESSION_PROOF"
    PATCH_PROPOSAL = "PATCH_PROPOSAL"
    PATCH_VALIDATION = "PATCH_VALIDATION"
    PATCH_APPLICATION = "PATCH_APPLICATION"
    REGRESSION_VERIFICATION = "REGRESSION_VERIFICATION"
    BASELINE_VERIFICATION = "BASELINE_VERIFICATION"
    SOURCE_INTEGRITY = "SOURCE_INTEGRITY"
    FINAL_VERDICT = "FINAL_VERDICT"
    AUDIT = "AUDIT"


def scrub_secrets(text: str) -> str:
    """Scrub sensitive credentials, tokens, and secret strings from evidence payloads."""
    if not text:
        return text

    scrubbed = text
    # Known secret environment keys and generic tokens
    patterns = [
        (
            re.compile(r"(nebius[-_]api[-_]key[:=\s]+)[^\s,;]+", re.IGNORECASE),
            r"\1[SCRUBBED_SECRET]",
        ),
        (
            re.compile(r"(supabase[-_]service[-_]role[-_]key[:=\s]+)[^\s,;]+", re.IGNORECASE),
            r"\1[SCRUBBED_SECRET]",
        ),
        (
            re.compile(r"(supabase[-_]anon[-_]key[:=\s]+)[^\s,;]+", re.IGNORECASE),
            r"\1[SCRUBBED_SECRET]",
        ),
        (re.compile(r"(bearer\s+)[a-zA-Z0-9_\-\.]{16,}", re.IGNORECASE), r"\1[SCRUBBED_TOKEN]"),
        (re.compile(r"(ghp_[a-zA-Z0-9]{36})", re.IGNORECASE), r"[SCRUBBED_GITHUB_TOKEN]"),
        (re.compile(r"(AKIA[0-9A-Z]{16})", re.IGNORECASE), r"[SCRUBBED_AWS_KEY]"),
        (re.compile(r"(password[:=\s]+)[^\s,;]+", re.IGNORECASE), r"\1[SCRUBBED_PASSWORD]"),
    ]

    for pat, repl in patterns:
        scrubbed = pat.sub(repl, scrubbed)

    return scrubbed


def sanitize_dict_secrets(obj: Any) -> Any:
    """Recursively scrub sensitive keys and credential values in nested dictionary data."""
    sensitive_keys = {
        "password",
        "secret",
        "nebius_api_key",
        "supabase_service_role_key",
        "supabase_anon_key",
        "token",
        "api_key",
    }
    if isinstance(obj, dict):
        clean: dict[str, Any] = {}
        for k, v in obj.items():
            if any(s in k.lower() for s in sensitive_keys):
                clean[k] = "[SCRUBBED_SECRET]"
            else:
                clean[k] = sanitize_dict_secrets(v)
        return clean
    if isinstance(obj, list):
        return [sanitize_dict_secrets(item) for item in obj]
    if isinstance(obj, str):
        return scrub_secrets(obj)
    return obj


def compute_content_sha256(data: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 digest from canonical JSON representation."""
    clean_data = sanitize_dict_secrets(data)
    canonical_json = json.dumps(clean_data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class EvidenceItem(BaseModel):
    """Atomic, immutable evidence unit with explicit provenance and cryptographic content digest."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    evidence_type: EvidenceType
    provenance: EvidenceProvenance
    source_phase: int
    source_entity_type: str
    source_entity_id: UUID | None = None
    title: str
    description: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    content_sha256: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def compute_bundle_sha256(investigation_id: UUID, verdict: str, items: list[EvidenceItem]) -> str:
    """Compute aggregate bundle SHA-256 fingerprint over the ordered evidence chain."""
    hasher = hashlib.sha256()
    hasher.update(str(investigation_id).encode("utf-8"))
    hasher.update(verdict.encode("utf-8"))
    for item in sorted(items, key=lambda x: (x.source_phase, x.evidence_type.value, str(x.id))):
        hasher.update(item.content_sha256.encode("utf-8"))
    return hasher.hexdigest()


class EvidenceBundle(BaseModel):
    """Aggregate, cryptographically fingerprinted evidence bundle representing the complete proof chain."""

    model_config = ConfigDict(frozen=True)

    bundle_id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    verdict: str  # Phase 6 authoritative verdict ("VERIFIED" | "UNVERIFIED" | "PENDING")
    bundle_sha256: str
    investigation: dict[str, Any] | None = None
    repository: dict[str, Any] | None = None
    reproduction: dict[str, Any] | None = None
    hypothesis: dict[str, Any] | None = None
    regression: dict[str, Any] | None = None
    patch: dict[str, Any] | None = None
    verification: dict[str, Any] | None = None
    evidence_items: list[EvidenceItem] = Field(default_factory=list)


class EvidenceHashResponse(BaseModel):
    """Lightweight integrity verification response."""

    model_config = ConfigDict(frozen=True)

    investigation_id: UUID
    bundle_sha256: str
    generated_at: datetime
