"""Evidence Bundle, Provenance & Audit Domain Service (Phase 7)

Assembles the complete, immutable, cryptographically fingerprinted EVIDA Evidence Bundle
from persisted database records across Phases 1–6 without re-executing sandbox jobs or calling AI.
Strictly distinguishes AI proposals from deterministic execution evidence.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.config import Settings
from app.core.logging import get_logger
from app.domain.evidence.models import (
    EvidenceBundle,
    EvidenceHashResponse,
    EvidenceItem,
    EvidenceProvenance,
    EvidenceType,
    compute_bundle_sha256,
    compute_content_sha256,
    sanitize_dict_secrets,
    scrub_secrets,
)
from app.domain.investigations.models import EventType, InvestigationStatus
from app.domain.investigations.repository import InvestigationRepository
from app.domain.investigations.service import InvestigationService
from app.domain.investigations.state_machine import InvestigationNotFoundError, LifecycleException

logger = get_logger("evida.evidence.service")


class EvidenceService:
    """Orchestrates aggregation, provenance classification, and cryptographic hashing of evidence."""

    def __init__(
        self,
        repo: InvestigationRepository,
        investigation_service: InvestigationService,
        settings: Settings,
    ) -> None:
        self.repo = repo
        self.investigation_service = investigation_service
        self.settings = settings

    async def get_or_build_evidence_bundle(
        self, investigation_id: UUID, user_id: str | None = None
    ) -> EvidenceBundle:
        """Assembles or retrieves the complete, tamper-evident evidence bundle for an investigation."""
        inv = await self.repo.get_by_id(investigation_id)
        if inv is None:
            raise InvestigationNotFoundError(str(investigation_id))

        if user_id is not None and inv.user_id and inv.user_id != user_id:
            raise LifecycleException(
                f"Investigation '{investigation_id}' does not belong to authenticated user/tenant.",
                code="INVESTIGATION_PRECONDITION_FAILED",
                status_code=403,
            )

        # 1. Fetch persisted evidence across all phases
        repo_meta = await self.repo.get_repository_by_investigation_id(investigation_id)
        repro = await self.repo.get_reproduction_run_by_investigation_id(investigation_id)
        hypo = await self.repo.get_hypothesis_by_investigation_id(investigation_id)
        reg = await self.repo.get_regression_test_by_investigation_id(investigation_id)
        patch = await self.repo.get_patch_candidate_by_investigation_id(investigation_id)
        verify_run = await self.repo.get_patch_verification_run_by_investigation_id(
            investigation_id
        )

        # 2. Build structured evidence items
        items: list[EvidenceItem] = []
        now = datetime.now(UTC)

        # Stage 1: Incident Description (Phase 1)
        inc_data = sanitize_dict_secrets(
            {
                "title": inv.title,
                "bug_description": inv.bug_description,
                "status": (inv.status.value if hasattr(inv.status, "value") else str(inv.status)),
            }
        )
        items.append(
            EvidenceItem(
                id=uuid4(),
                investigation_id=investigation_id,
                evidence_type=EvidenceType.INCIDENT,
                provenance=EvidenceProvenance.SYSTEM_METADATA,
                source_phase=1,
                source_entity_type="investigation",
                source_entity_id=inv.id,
                title="Incident Bug Report",
                description="Initial software defect report submitted for repair investigation.",
                data=inc_data,
                content_sha256=compute_content_sha256(inc_data),
                created_at=inv.created_at,
            )
        )

        # Stage 2: Repository Ingestion (Phase 2)
        if repo_meta is not None:
            repo_data = {
                "repository_id": str(repo_meta.id),
                "name": repo_meta.name,
                "archive_sha256": repo_meta.archive_sha256,
                "archive_size_bytes": repo_meta.archive_size_bytes,
                "status": (
                    repo_meta.status.value
                    if hasattr(repo_meta.status, "value")
                    else str(repo_meta.status)
                ),
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.REPOSITORY,
                    provenance=EvidenceProvenance.CRYPTOGRAPHIC_INTEGRITY,
                    source_phase=2,
                    source_entity_type="repository",
                    source_entity_id=repo_meta.id,
                    title="Source Repository Archive Ingestion",
                    description="Cryptographically fingerprinted repository archive payload.",
                    data=repo_data,
                    content_sha256=compute_content_sha256(repo_data),
                    created_at=now,
                )
            )

        # Stage 3: Failure Reproduction (Phase 2)
        if repro is not None:
            repro_data = {
                "command": repro.command,
                "exit_code": repro.exit_code,
                "status": (
                    repro.status.value if hasattr(repro.status, "value") else str(repro.status)
                ),
                "duration_ms": repro.duration_ms,
                "stdout": scrub_secrets(repro.stdout),
                "stderr": scrub_secrets(repro.stderr),
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.REPRODUCTION,
                    provenance=EvidenceProvenance.DETERMINISTIC_EXECUTION,
                    source_phase=2,
                    source_entity_type="reproduction_run",
                    source_entity_id=repro.id,
                    title="Failure Reproduction Execution",
                    description="Isolated sandbox execution reproducing bug report against original code.",
                    data=repro_data,
                    content_sha256=compute_content_sha256(repro_data),
                    created_at=now,
                )
            )

        # Stage 4: AI Hypothesis (Phase 3 — AI Proposal)
        if hypo is not None:
            hypo_data = {
                "model": hypo.model,
                "provider": hypo.provider,
                "hypothesis": hypo.hypothesis,
                "confidence": hypo.confidence,
                "root_cause": hypo.root_cause,
                "affected_files": hypo.affected_files,
                "observations": hypo.evidence,
                "recommended_next_action": hypo.recommended_next_action,
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.HYPOTHESIS,
                    provenance=EvidenceProvenance.AI_PROPOSAL,
                    source_phase=3,
                    source_entity_type="investigation_hypothesis",
                    source_entity_id=hypo.id,
                    title="AI Proposed Causal Hypothesis",
                    description="AI-synthesized defect root cause explanation. Untrusted proposal until proven.",
                    data=hypo_data,
                    content_sha256=compute_content_sha256(hypo_data),
                    created_at=now,
                )
            )

        # Stage 5: Regression Test (Phase 4 — AI Proposal)
        if reg is not None:
            reg_prop_data = {
                "test_path": reg.test_path,
                "framework": reg.framework,
                "target_symbol": reg.target_symbol,
                "target_file": reg.target_file,
                "description": reg.description,
                "test_content": reg.test_content,
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.REGRESSION_TEST,
                    provenance=EvidenceProvenance.AI_PROPOSAL,
                    source_phase=4,
                    source_entity_type="investigation_regression_test",
                    source_entity_id=reg.id,
                    title="AI Proposed Regression Test",
                    description="AI-generated pytest regression test asserting expected behavior.",
                    data=reg_prop_data,
                    content_sha256=compute_content_sha256(reg_prop_data),
                    created_at=now,
                )
            )

            # Stage 6: Regression Proof (Phase 4 — Deterministic Execution)
            reg_proof_data = {
                "verification_status": (
                    str(reg.verification_status.value)
                    if reg.verification_status and hasattr(reg.verification_status, "value")
                    else str(reg.verification_status or "PENDING")
                ),
                "target_symbol": reg.target_symbol,
                "target_file": reg.target_file,
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.REGRESSION_PROOF,
                    provenance=EvidenceProvenance.DETERMINISTIC_EXECUTION,
                    source_phase=4,
                    source_entity_type="investigation_regression_test",
                    source_entity_id=reg.id,
                    title="Regression Test Verification (Pre-Patch)",
                    description="Deterministic execution of generated regression test against unpatched codebase.",
                    data=reg_proof_data,
                    content_sha256=compute_content_sha256(reg_proof_data),
                    created_at=now,
                )
            )

        # Stage 7: Patch Proposal (Phase 5 — AI Proposal)
        if patch is not None:
            patch_prop_data = {
                "patch_content": patch.patch_content,
                "changed_files": patch.changed_files,
                "reasoning": patch.reasoning,
                "description": patch.description,
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.PATCH_PROPOSAL,
                    provenance=EvidenceProvenance.AI_PROPOSAL,
                    source_phase=5,
                    source_entity_type="patch_candidate",
                    source_entity_id=patch.id,
                    title="AI Proposed Patch Candidate",
                    description="AI-generated unified diff patch designed to fix the verified defect.",
                    data=patch_prop_data,
                    content_sha256=compute_content_sha256(patch_prop_data),
                    created_at=now,
                )
            )

            # Stage 8: Patch Validation (Phase 5 — Deterministic Execution)
            patch_val_data = {
                "status": (
                    patch.status.value if hasattr(patch.status, "value") else str(patch.status)
                ),
                "validation_result": str(patch.validation_result),
                "validation_errors": patch.validation_errors,
                "changed_files": patch.changed_files,
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.PATCH_VALIDATION,
                    provenance=EvidenceProvenance.DETERMINISTIC_EXECUTION,
                    source_phase=5,
                    source_entity_type="patch_candidate",
                    source_entity_id=patch.id,
                    title="Patch Structural & Scope Validation",
                    description="Deterministic AST, diff hunk, and test immutability safety check.",
                    data=patch_val_data,
                    content_sha256=compute_content_sha256(patch_val_data),
                    created_at=now,
                )
            )

        # Stage 9-13: Deterministic Double Validation (Phase 6)
        authoritative_verdict = "PENDING"
        if verify_run is not None:
            authoritative_verdict = (
                verify_run.verdict.value
                if hasattr(verify_run.verdict, "value")
                else str(verify_run.verdict)
            )

            # 9. Patch Application
            app_data = {
                "status": verify_run.patch_application_status,
                "exit_code": verify_run.patch_application_exit_code,
                "stdout": scrub_secrets(verify_run.patch_application_stdout),
                "stderr": scrub_secrets(verify_run.patch_application_stderr),
                "workspace_manifest": verify_run.workspace_file_manifest,
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.PATCH_APPLICATION,
                    provenance=EvidenceProvenance.DETERMINISTIC_EXECUTION,
                    source_phase=6,
                    source_entity_type="patch_verification_run",
                    source_entity_id=verify_run.id,
                    title="Patch Application in Fresh Workspace",
                    description="Applying candidate unified diff inside fresh isolated ephemeral sandbox.",
                    data=app_data,
                    content_sha256=compute_content_sha256(app_data),
                    created_at=now,
                )
            )

            # 10. Regression Verification (Post-Patch)
            reg_ver_data = {
                "status": verify_run.regression_status,
                "exit_code": verify_run.regression_exit_code,
                "duration_ms": verify_run.regression_duration_ms,
                "stdout": scrub_secrets(verify_run.regression_stdout),
                "stderr": scrub_secrets(verify_run.regression_stderr),
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.REGRESSION_VERIFICATION,
                    provenance=EvidenceProvenance.DETERMINISTIC_EXECUTION,
                    source_phase=6,
                    source_entity_type="patch_verification_run",
                    source_entity_id=verify_run.id,
                    title="Regression Test Rerun (Post-Patch)",
                    description="Executing proven regression test against the patched workspace.",
                    data=reg_ver_data,
                    content_sha256=compute_content_sha256(reg_ver_data),
                    created_at=now,
                )
            )

            # 11. Baseline Verification
            base_data = {
                "status": verify_run.baseline_status,
                "command": verify_run.baseline_command,
                "exit_code": verify_run.baseline_exit_code,
                "duration_ms": verify_run.baseline_duration_ms,
                "stdout": scrub_secrets(verify_run.baseline_stdout),
                "stderr": scrub_secrets(verify_run.baseline_stderr),
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.BASELINE_VERIFICATION,
                    provenance=EvidenceProvenance.DETERMINISTIC_EXECUTION,
                    source_phase=6,
                    source_entity_type="patch_verification_run",
                    source_entity_id=verify_run.id,
                    title="Repository Baseline Suite Verification",
                    description="Executing existing repository test suite to guarantee zero regression.",
                    data=base_data,
                    content_sha256=compute_content_sha256(base_data),
                    created_at=now,
                )
            )

            # 12. Source Integrity Check
            source_data = {
                "repository_sha256": verify_run.repository_sha256,
                "source_integrity_verified": (
                    verify_run.failure_classification != "SOURCE_INTEGRITY_VIOLATION"
                ),
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.SOURCE_INTEGRITY,
                    provenance=EvidenceProvenance.CRYPTOGRAPHIC_INTEGRITY,
                    source_phase=6,
                    source_entity_type="patch_verification_run",
                    source_entity_id=verify_run.id,
                    title="Source Repository Cryptographic Immutability",
                    description="Cryptographic SHA-256 confirmation that stored repository archive was unchanged.",
                    data=source_data,
                    content_sha256=compute_content_sha256(source_data),
                    created_at=now,
                )
            )

            # 13. Final Verdict
            verdict_data = {
                "verdict": authoritative_verdict,
                "failure_classification": (
                    str(verify_run.failure_classification)
                    if verify_run.failure_classification
                    else None
                ),
            }
            items.append(
                EvidenceItem(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    evidence_type=EvidenceType.FINAL_VERDICT,
                    provenance=EvidenceProvenance.DETERMINISTIC_EXECUTION,
                    source_phase=6,
                    source_entity_type="patch_verification_run",
                    source_entity_id=verify_run.id,
                    title="Double Validation Final Verdict",
                    description="Deterministic conclusion derived exclusively from execution evidence.",
                    data=verdict_data,
                    content_sha256=compute_content_sha256(verdict_data),
                    created_at=now,
                )
            )
        elif inv.status == InvestigationStatus.FAILED:
            authoritative_verdict = "FAILED"
        elif inv.status == InvestigationStatus.COMPLETED:
            authoritative_verdict = "VERIFIED"

        # 3. Persist items to append-only evidence store
        await self.repo.save_evidence_items(items)

        # 4. Calculate aggregate bundle SHA-256 fingerprint
        bundle_sha256 = compute_bundle_sha256(investigation_id, authoritative_verdict, items)

        # 5. Emit audit event
        await self.investigation_service.record_event(
            investigation_id=investigation_id,
            event_type=EventType.EVIDENCE_BUNDLE_GENERATED,
            from_status=inv.status,
            to_status=inv.status,
            metadata={
                "bundle_sha256": bundle_sha256,
                "evidence_items_count": len(items),
                "authoritative_verdict": authoritative_verdict,
            },
        )

        # 6. Return structured aggregate bundle
        return EvidenceBundle(
            bundle_id=uuid4(),
            investigation_id=investigation_id,
            generated_at=now,
            verdict=authoritative_verdict,
            bundle_sha256=bundle_sha256,
            investigation=inc_data,
            repository=repo_data if repo_meta is not None else None,
            reproduction=repro_data if repro is not None else None,
            hypothesis=hypo_data if hypo is not None else None,
            regression=reg_prop_data if reg is not None else None,
            patch=patch_prop_data if patch is not None else None,
            verification=(
                {
                    "verdict": authoritative_verdict,
                    "patch_application": verify_run.patch_application_status,
                    "regression_status": verify_run.regression_status,
                    "baseline_status": verify_run.baseline_status,
                    "source_integrity_verified": (
                        verify_run.failure_classification != "SOURCE_INTEGRITY_VIOLATION"
                    ),
                    "failure_classification": (
                        str(verify_run.failure_classification)
                        if verify_run.failure_classification
                        else None
                    ),
                }
                if verify_run is not None
                else None
            ),
            evidence_items=items,
        )

    async def list_evidence_items(
        self, investigation_id: UUID, user_id: str | None = None
    ) -> list[EvidenceItem]:
        """Retrieve the sequence of individual evidence items."""
        bundle = await self.get_or_build_evidence_bundle(investigation_id, user_id=user_id)
        return bundle.evidence_items

    async def get_bundle_hash(
        self, investigation_id: UUID, user_id: str | None = None
    ) -> EvidenceHashResponse:
        """Retrieve lightweight bundle hash and generation timestamp."""
        bundle = await self.get_or_build_evidence_bundle(investigation_id, user_id=user_id)
        return EvidenceHashResponse(
            investigation_id=investigation_id,
            bundle_sha256=bundle.bundle_sha256,
            generated_at=bundle.generated_at,
        )

    async def export_bundle_json(self, investigation_id: UUID, user_id: str | None = None) -> str:
        """Export canonical formatted JSON payload of the complete evidence bundle."""
        bundle = await self.get_or_build_evidence_bundle(investigation_id, user_id=user_id)
        # Emit access/export event
        inv = await self.repo.get_by_id(investigation_id)
        if inv is not None:
            await self.investigation_service.record_event(
                investigation_id=investigation_id,
                event_type=EventType.EVIDENCE_BUNDLE_EXPORTED,
                from_status=inv.status,
                to_status=inv.status,
                metadata={"bundle_sha256": bundle.bundle_sha256},
            )
        return json.dumps(bundle.model_dump(mode="json"), indent=2, sort_keys=True)
