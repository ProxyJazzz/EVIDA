"""Unit tests for Phase 7 Evidence Bundle, Provenance & Audit System."""

from __future__ import annotations

import hashlib
import time
from uuid import uuid4

import pytest
from app.core.config import Settings
from app.domain.evidence.evidence_service import EvidenceService
from app.domain.evidence.models import (
    EvidenceItem,
    EvidenceProvenance,
    EvidenceType,
    compute_bundle_sha256,
    compute_content_sha256,
    sanitize_dict_secrets,
    scrub_secrets,
)
from app.domain.investigations.models import (
    EventType,
    Investigation,
    InvestigationEvent,
    InvestigationHypothesisRecord,
    InvestigationRegressionTestRecord,
    InvestigationStatus,
    RegressionVerificationStatus,
)
from app.domain.investigations.repository import InMemoryInvestigationRepository
from app.domain.investigations.service import InvestigationService
from app.domain.investigations.state_machine import LifecycleException
from app.domain.patches.models import PatchCandidateRecord, PatchCandidateStatus
from app.domain.repositories.models import (
    Repository,
    RepositoryStatus,
    ReproductionRun,
    ReproductionStatus,
)
from app.domain.verification.models import (
    PatchVerificationRun,
    PatchVerificationStatus,
    PatchVerificationVerdict,
    VerificationFailureClassification,
)


def test_scrub_secrets():
    raw_text = (
        "Config: NEBIUS_API_KEY=secret_key_123456789 and "
        "SUPABASE_SERVICE_ROLE_KEY: eyJhbGciOiJIUzI1NiJ9.secret "
        "Bearer abcdef1234567890abcdef and password=super_secret!"
    )
    scrubbed = scrub_secrets(raw_text)
    assert "secret_key_123456789" not in scrubbed
    assert "[SCRUBBED_SECRET]" in scrubbed
    assert "super_secret!" not in scrubbed
    assert "[SCRUBBED_PASSWORD]" in scrubbed
    assert "[SCRUBBED_TOKEN]" in scrubbed


def test_sanitize_dict_secrets():
    payload = {
        "user": "developer",
        "api_key": "raw_secret_key",
        "env": {"password": "mypassword", "nested": {"token": "secret_token_123"}},
        "logs": "Connected with bearer abcdef1234567890abcdef",
    }
    clean = sanitize_dict_secrets(payload)
    assert clean["api_key"] == "[SCRUBBED_SECRET]"
    assert clean["env"]["password"] == "[SCRUBBED_SECRET]"
    assert clean["env"]["nested"]["token"] == "[SCRUBBED_SECRET]"
    assert "abcdef1234567890abcdef" not in clean["logs"]


def test_compute_content_sha256_determinism():
    data1 = {"b": 2, "a": 1, "nested": {"y": "yes", "x": "no"}}
    data2 = {"a": 1, "b": 2, "nested": {"x": "no", "y": "yes"}}
    hash1 = compute_content_sha256(data1)
    hash2 = compute_content_sha256(data2)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_compute_bundle_sha256_sensitivity():
    inv_id = uuid4()
    item1 = EvidenceItem(
        id=uuid4(),
        investigation_id=inv_id,
        evidence_type=EvidenceType.INCIDENT,
        provenance=EvidenceProvenance.SYSTEM_METADATA,
        source_phase=1,
        source_entity_type="investigation",
        title="Incident",
        data={"bug": "divide bug"},
        content_sha256=compute_content_sha256({"bug": "divide bug"}),
    )
    item2 = EvidenceItem(
        id=uuid4(),
        investigation_id=inv_id,
        evidence_type=EvidenceType.REPRODUCTION,
        provenance=EvidenceProvenance.DETERMINISTIC_EXECUTION,
        source_phase=2,
        source_entity_type="reproduction_run",
        title="Repro",
        data={"exit": 1},
        content_sha256=compute_content_sha256({"exit": 1}),
    )

    bundle_hash1 = compute_bundle_sha256(inv_id, "VERIFIED", [item1, item2])
    bundle_hash2 = compute_bundle_sha256(
        inv_id, "VERIFIED", [item2, item1]
    )  # order invariant
    assert bundle_hash1 == bundle_hash2

    # Mutation produces different hash
    item2_mutated = EvidenceItem(
        id=uuid4(),
        investigation_id=inv_id,
        evidence_type=EvidenceType.REPRODUCTION,
        provenance=EvidenceProvenance.DETERMINISTIC_EXECUTION,
        source_phase=2,
        source_entity_type="reproduction_run",
        title="Repro",
        data={"exit": 0},
        content_sha256=compute_content_sha256({"exit": 0}),
    )
    bundle_hash_mutated = compute_bundle_sha256(
        inv_id, "VERIFIED", [item1, item2_mutated]
    )
    assert bundle_hash1 != bundle_hash_mutated


@pytest.mark.asyncio
async def test_evidence_service_bundle_generation():
    repo = InMemoryInvestigationRepository()
    inv_svc = InvestigationService(repo)
    settings = Settings()
    ev_svc = EvidenceService(repo, inv_svc, settings)

    inv_id = uuid4()
    repo_id = uuid4()

    # 1. Seed completed verified investigation
    inv = Investigation(
        id=inv_id,
        user_id="user_123",
        project_id=uuid4(),
        repository_id=repo_id,
        title="Divide by zero error",
        bug_description="Evaluation fails",
        status=InvestigationStatus.COMPLETED,
    )
    event = InvestigationEvent(
        id=uuid4(),
        investigation_id=inv_id,
        event_type=EventType.INVESTIGATION_CREATED,
        from_status=None,
        to_status=InvestigationStatus.CREATED,
    )
    await repo.create(inv, event)

    # 2. Seed Repository
    await repo.save_repository(
        Repository(
            id=repo_id,
            investigation_id=inv_id,
            name="calculator.zip",
            storage_path="test/calculator.zip",
            archive_size_bytes=2048,
            archive_sha256="fa4aec473a843aa4d3a2df0840c192a2e28526c6f5d146b0ae7b7fabaf5280a9",
            status=RepositoryStatus.READY,
        )
    )

    # 3. Seed Reproduction
    repro = ReproductionRun(
        id=uuid4(),
        investigation_id=inv_id,
        repository_id=repo_id,
        command="pytest tests/test_bug.py",
        status=ReproductionStatus.REPRODUCED,
        exit_code=1,
        stdout="FAILED assert 20 == 5",
        stderr="",
        duration_ms=120,
        timed_out=False,
    )
    await repo.save_reproduction_run(repro)

    # 4. Seed Hypothesis
    hypo = InvestigationHypothesisRecord(
        id=uuid4(),
        investigation_id=inv_id,
        reproduction_run_id=repro.id,
        hypothesis="Divide function multiplies operands",
        confidence=0.99,
        model="nvidia/Nemotron-3_5-Lightning",
        provider="nebius",
        root_cause={
            "file": "src/calculator.py",
            "symbol": "divide",
            "line": 2,
            "description": "Multiplication bug in divide",
        },
        affected_files=["src/calculator.py"],
        evidence=["Returns 20 instead of 5"],
        recommended_next_action="Generate regression test",
    )
    await repo.save_hypothesis(hypo)

    # 5. Seed Regression Test
    reg = InvestigationRegressionTestRecord(
        id=uuid4(),
        investigation_id=inv_id,
        hypothesis_id=hypo.id,
        test_path="tests/test_regression.py",
        framework="pytest",
        language="python",
        description="Verify divide returns 5",
        test_content="def test_regression(): assert divide(10, 2) == 5\n",
        target_symbol="divide",
        target_file="src/calculator.py",
        expected_failure_reason="Returns 20 instead of 5",
        verification_status=RegressionVerificationStatus.REGRESSION_PROVEN,
    )
    await repo.save_regression_test(reg)

    # 6. Seed Patch Candidate
    patch_rec = PatchCandidateRecord(
        id=uuid4(),
        investigation_id=inv_id,
        hypothesis_id=hypo.id,
        regression_test_id=reg.id,
        status=PatchCandidateStatus.VALIDATED,
        description="Fix divide implementation",
        patch_format="unified_diff",
        patch_content="--- a/src/calculator.py\n+++ b/src/calculator.py\n@@ -1,2 +1,2 @@\n-    return a * b\n+    return a / b\n",
        changed_files=["src/calculator.py"],
        change_summary=[{"file": "src/calculator.py", "reason": "Change * to /"}],
        reasoning="Multiplication bug",
    )
    await repo.save_patch_candidate(patch_rec)

    # 7. Seed Verification Run
    v_run = PatchVerificationRun(
        id=uuid4(),
        investigation_id=inv_id,
        patch_candidate_id=patch_rec.id,
        regression_test_id=reg.id,
        status=PatchVerificationStatus.VERIFIED,
        patch_sha256=hashlib.sha256(patch_rec.patch_content.encode()).hexdigest(),
        repository_sha256="fa4aec473a843aa4d3a2df0840c192a2e28526c6f5d146b0ae7b7fabaf5280a9",
        patch_application_status="APPLIED",
        patch_application_exit_code=0,
        patch_application_stdout="Patch applied cleanly",
        patch_application_stderr="",
        regression_status="PASSED",
        regression_exit_code=0,
        regression_stdout="1 passed",
        regression_stderr="",
        regression_duration_ms=50,
        baseline_status="PASSED",
        baseline_command="pytest",
        baseline_exit_code=0,
        baseline_stdout="2 passed",
        baseline_stderr="",
        baseline_duration_ms=75,
        verdict=PatchVerificationVerdict.VERIFIED,
        failure_classification=None,
    )
    await repo.save_patch_verification_run(v_run)

    # Build Bundle
    start = time.perf_counter()
    bundle = await ev_svc.get_or_build_evidence_bundle(inv_id, user_id="user_123")
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    # Performance boundary: generation < 500ms
    assert elapsed_ms < 500.0

    # Bundle assertions
    assert bundle.investigation_id == inv_id
    assert bundle.verdict == "VERIFIED"
    assert len(bundle.bundle_sha256) == 64
    assert len(bundle.evidence_items) == 13

    # Provenance correctness check
    types = {item.evidence_type: item.provenance for item in bundle.evidence_items}
    assert types[EvidenceType.INCIDENT] == EvidenceProvenance.SYSTEM_METADATA
    assert types[EvidenceType.REPOSITORY] == EvidenceProvenance.CRYPTOGRAPHIC_INTEGRITY
    assert (
        types[EvidenceType.REPRODUCTION] == EvidenceProvenance.DETERMINISTIC_EXECUTION
    )
    assert types[EvidenceType.HYPOTHESIS] == EvidenceProvenance.AI_PROPOSAL
    assert types[EvidenceType.REGRESSION_TEST] == EvidenceProvenance.AI_PROPOSAL
    assert (
        types[EvidenceType.REGRESSION_PROOF]
        == EvidenceProvenance.DETERMINISTIC_EXECUTION
    )
    assert types[EvidenceType.PATCH_PROPOSAL] == EvidenceProvenance.AI_PROPOSAL
    assert (
        types[EvidenceType.PATCH_VALIDATION]
        == EvidenceProvenance.DETERMINISTIC_EXECUTION
    )
    assert (
        types[EvidenceType.PATCH_APPLICATION]
        == EvidenceProvenance.DETERMINISTIC_EXECUTION
    )
    assert (
        types[EvidenceType.REGRESSION_VERIFICATION]
        == EvidenceProvenance.DETERMINISTIC_EXECUTION
    )
    assert (
        types[EvidenceType.BASELINE_VERIFICATION]
        == EvidenceProvenance.DETERMINISTIC_EXECUTION
    )
    assert (
        types[EvidenceType.SOURCE_INTEGRITY]
        == EvidenceProvenance.CRYPTOGRAPHIC_INTEGRITY
    )
    assert (
        types[EvidenceType.FINAL_VERDICT] == EvidenceProvenance.DETERMINISTIC_EXECUTION
    )


@pytest.mark.asyncio
async def test_evidence_service_unverified_investigation():
    repo = InMemoryInvestigationRepository()
    inv_svc = InvestigationService(repo)
    settings = Settings()
    ev_svc = EvidenceService(repo, inv_svc, settings)

    inv_id = uuid4()
    repo_id = uuid4()

    inv = Investigation(
        id=inv_id,
        user_id="user_123",
        project_id=uuid4(),
        repository_id=repo_id,
        title="Unverified defect",
        status=InvestigationStatus.VERIFYING,
    )
    await repo.create(
        inv,
        InvestigationEvent(
            id=uuid4(),
            investigation_id=inv_id,
            event_type=EventType.INVESTIGATION_CREATED,
            to_status=InvestigationStatus.CREATED,
        ),
    )

    # Verification run that failed double validation (baseline broke)
    v_run = PatchVerificationRun(
        id=uuid4(),
        investigation_id=inv_id,
        patch_candidate_id=uuid4(),
        regression_test_id=uuid4(),
        status=PatchVerificationStatus.UNVERIFIED,
        patch_sha256="abc",
        repository_sha256="123",
        patch_application_status="APPLIED",
        patch_application_exit_code=0,
        patch_application_stdout="",
        patch_application_stderr="",
        regression_status="PASSED",
        regression_exit_code=0,
        regression_stdout="",
        regression_stderr="",
        regression_duration_ms=40,
        baseline_status="FAILED",
        baseline_command="pytest",
        baseline_exit_code=1,
        baseline_stdout="1 failed",
        baseline_stderr="",
        baseline_duration_ms=80,
        verdict=PatchVerificationVerdict.UNVERIFIED,
        failure_classification=VerificationFailureClassification.BASELINE_TEST_FAILURE,
    )
    await repo.save_patch_verification_run(v_run)

    bundle = await ev_svc.get_or_build_evidence_bundle(inv_id)
    assert bundle.verdict == "UNVERIFIED"
    final_verdict_item = next(
        i
        for i in bundle.evidence_items
        if i.evidence_type == EvidenceType.FINAL_VERDICT
    )
    assert final_verdict_item.data["verdict"] == "UNVERIFIED"
    assert final_verdict_item.data["failure_classification"] == "BASELINE_TEST_FAILURE"


@pytest.mark.asyncio
async def test_evidence_service_tenant_isolation():
    repo = InMemoryInvestigationRepository()
    inv_svc = InvestigationService(repo)
    ev_svc = EvidenceService(repo, inv_svc, Settings())

    inv_id = uuid4()
    inv = Investigation(
        id=inv_id,
        user_id="user_A",
        project_id=uuid4(),
        repository_id=uuid4(),
        title="Secret project",
        status=InvestigationStatus.CREATED,
    )
    await repo.create(
        inv,
        InvestigationEvent(
            id=uuid4(),
            investigation_id=inv_id,
            event_type=EventType.INVESTIGATION_CREATED,
            to_status=InvestigationStatus.CREATED,
        ),
    )

    # User B cannot access User A's evidence
    with pytest.raises(LifecycleException) as exc_info:
        await ev_svc.get_or_build_evidence_bundle(inv_id, user_id="user_B")
    assert exc_info.value.code == "INVESTIGATION_PRECONDITION_FAILED"
    assert exc_info.value.status_code == 403
