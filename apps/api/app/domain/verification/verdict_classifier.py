"""Deterministic Verdict Classifier for Phase 6: Deterministic Patch Verification & Double Validation

Implements the objective Double Validation Rule:
1. Patch application must succeed cleanly without unexpected file mutations or test modifications.
2. Proven regression test must PASS after patch application.
3. Repository baseline test suite must PASS after patch application.
4. Cryptographic source integrity of original repository archive must be preserved.

AI confidence, opinions, or natural language assertions play zero role in verdict classification.
"""

from __future__ import annotations

from app.domain.verification.models import (
    PatchApplicationResult,
    PatchVerificationVerdict,
    VerificationFailureClassification,
)


def classify_patch_application_failure(
    app_result: PatchApplicationResult,
    *,
    timed_out: bool = False,
    policy_blocked: bool = False,
) -> VerificationFailureClassification:
    """Deterministically classify a patch application failure."""
    if policy_blocked:
        return VerificationFailureClassification.PATCH_APPLICATION_POLICY_BLOCKED
    if timed_out:
        return VerificationFailureClassification.PATCH_APPLICATION_TIMEOUT

    err_lower = (app_result.stderr or "").lower()
    if "unexpected" in err_lower or "security violation" in err_lower:
        return VerificationFailureClassification.UNEXPECTED_WORKSPACE_CHANGE

    return VerificationFailureClassification.PATCH_APPLICATION_FAILED


def classify_regression_failure(
    exit_code: int | None,
    *,
    timed_out: bool = False,
    policy_blocked: bool = False,
) -> VerificationFailureClassification:
    """Deterministically classify a regression test verification failure."""
    if policy_blocked:
        return VerificationFailureClassification.REGRESSION_POLICY_BLOCKED
    if timed_out:
        return VerificationFailureClassification.REGRESSION_TIMEOUT
    if exit_code == 1:
        # Standard test assertion failure against the patched workspace
        return VerificationFailureClassification.REGRESSION_STILL_FAILING
    # Any other exit code (e.g. import error, syntax error, SIGSEGV, nonzero setup)
    return VerificationFailureClassification.REGRESSION_EXECUTION_ERROR


def classify_baseline_failure(
    exit_code: int | None,
    *,
    timed_out: bool = False,
    policy_blocked: bool = False,
) -> VerificationFailureClassification:
    """Deterministically classify a baseline test suite verification failure."""
    if policy_blocked:
        return VerificationFailureClassification.BASELINE_POLICY_BLOCKED
    if timed_out:
        return VerificationFailureClassification.BASELINE_TIMEOUT
    if exit_code == 1:
        # Standard assertion failure in the repository's existing test suite
        return VerificationFailureClassification.BASELINE_TEST_FAILURE
    return VerificationFailureClassification.BASELINE_EXECUTION_ERROR


def determine_double_validation_verdict(
    *,
    patch_applied: bool,
    patch_classification: VerificationFailureClassification | None,
    regression_passed: bool,
    regression_classification: VerificationFailureClassification | None,
    baseline_passed: bool,
    baseline_classification: VerificationFailureClassification | None,
    source_integrity_intact: bool,
) -> tuple[PatchVerificationVerdict, VerificationFailureClassification | None]:
    """Execute the Double Validation Rule.

    Returns:
        (VERIFIED, None) iff patch applied cleanly AND regression test passed
        AND baseline test suite passed AND source integrity was preserved.
        Otherwise (UNVERIFIED, failure_classification).
    """
    if not patch_applied:
        return (
            PatchVerificationVerdict.UNVERIFIED,
            patch_classification or VerificationFailureClassification.PATCH_APPLICATION_FAILED,
        )

    if not regression_passed:
        return (
            PatchVerificationVerdict.UNVERIFIED,
            regression_classification or VerificationFailureClassification.REGRESSION_STILL_FAILING,
        )

    if not baseline_passed:
        return (
            PatchVerificationVerdict.UNVERIFIED,
            baseline_classification or VerificationFailureClassification.BASELINE_TEST_FAILURE,
        )

    if not source_integrity_intact:
        return (
            PatchVerificationVerdict.UNVERIFIED,
            VerificationFailureClassification.SOURCE_INTEGRITY_VIOLATION,
        )

    return (PatchVerificationVerdict.VERIFIED, None)
