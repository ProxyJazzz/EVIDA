"""Unit tests for Phase 6 Verdict Classifier and Double Validation Rules."""

from __future__ import annotations

from app.domain.verification.models import (
    PatchApplicationResult,
    PatchVerificationVerdict,
    VerificationFailureClassification,
)
from app.domain.verification.verdict_classifier import (
    classify_baseline_failure,
    classify_patch_application_failure,
    classify_regression_failure,
    determine_double_validation_verdict,
)


def test_classify_patch_application_failures():
    # Policy blocked
    res_policy = PatchApplicationResult(
        status="FAILED",
        exit_code=1,
        stdout="",
        stderr="Blocked by sandbox policy",
        duration_ms=10.0,
    )
    assert (
        classify_patch_application_failure(res_policy, policy_blocked=True)
        == VerificationFailureClassification.PATCH_APPLICATION_POLICY_BLOCKED
    )

    # Timeout
    res_timeout = PatchApplicationResult(
        status="TIMEOUT",
        exit_code=124,
        stdout="",
        stderr="Timed out",
        duration_ms=30000.0,
    )
    assert (
        classify_patch_application_failure(res_timeout, timed_out=True)
        == VerificationFailureClassification.PATCH_APPLICATION_TIMEOUT
    )

    # Unexpected workspace changes
    res_unexpected = PatchApplicationResult(
        status="FAILED",
        exit_code=1,
        stdout="",
        stderr="Unexpected workspace changes detected. Created: ['rogue.py']",
        duration_ms=15.0,
    )
    assert (
        classify_patch_application_failure(res_unexpected)
        == VerificationFailureClassification.UNEXPECTED_WORKSPACE_CHANGE
    )

    # Security violation (e.g. test file modification)
    res_sec = PatchApplicationResult(
        status="FAILED",
        exit_code=1,
        stdout="",
        stderr="Security violation: patch modified test file 'tests/test_x.py'",
        duration_ms=12.0,
    )
    assert (
        classify_patch_application_failure(res_sec)
        == VerificationFailureClassification.UNEXPECTED_WORKSPACE_CHANGE
    )

    # General hunk reject / malformed diff
    res_hunk = PatchApplicationResult(
        status="FAILED",
        exit_code=1,
        stdout="",
        stderr="Hunk context mismatch at line 4",
        duration_ms=5.0,
    )
    assert (
        classify_patch_application_failure(res_hunk)
        == VerificationFailureClassification.PATCH_APPLICATION_FAILED
    )


def test_classify_regression_failures():
    # Policy blocked
    assert (
        classify_regression_failure(None, policy_blocked=True)
        == VerificationFailureClassification.REGRESSION_POLICY_BLOCKED
    )

    # Timed out
    assert (
        classify_regression_failure(124, timed_out=True)
        == VerificationFailureClassification.REGRESSION_TIMEOUT
    )

    # Test assertion still failing (pytest exit code 1)
    assert (
        classify_regression_failure(1)
        == VerificationFailureClassification.REGRESSION_STILL_FAILING
    )

    # Test execution error / crash / collection error (pytest exit code 2 or error)
    assert (
        classify_regression_failure(2)
        == VerificationFailureClassification.REGRESSION_EXECUTION_ERROR
    )
    assert (
        classify_regression_failure(-1)
        == VerificationFailureClassification.REGRESSION_EXECUTION_ERROR
    )


def test_classify_baseline_failures():
    # Policy blocked
    assert (
        classify_baseline_failure(None, policy_blocked=True)
        == VerificationFailureClassification.BASELINE_POLICY_BLOCKED
    )

    # Timed out
    assert (
        classify_baseline_failure(124, timed_out=True)
        == VerificationFailureClassification.BASELINE_TIMEOUT
    )

    # Assertion failure in existing suite (exit code 1)
    assert (
        classify_baseline_failure(1)
        == VerificationFailureClassification.BASELINE_TEST_FAILURE
    )

    # Crash / collection error in baseline suite
    assert (
        classify_baseline_failure(2)
        == VerificationFailureClassification.BASELINE_EXECUTION_ERROR
    )
    assert (
        classify_baseline_failure(-1)
        == VerificationFailureClassification.BASELINE_EXECUTION_ERROR
    )


def test_determine_double_validation_verdict_matrix():
    # Happy path: everything passes + source integrity preserved
    verdict, failure = determine_double_validation_verdict(
        patch_applied=True,
        patch_classification=None,
        regression_passed=True,
        regression_classification=None,
        baseline_passed=True,
        baseline_classification=None,
        source_integrity_intact=True,
    )
    assert verdict == PatchVerificationVerdict.VERIFIED
    assert failure is None

    # Patch application failed
    verdict, failure = determine_double_validation_verdict(
        patch_applied=False,
        patch_classification=VerificationFailureClassification.PATCH_APPLICATION_FAILED,
        regression_passed=False,
        regression_classification=None,
        baseline_passed=False,
        baseline_classification=None,
        source_integrity_intact=True,
    )
    assert verdict == PatchVerificationVerdict.UNVERIFIED
    assert failure == VerificationFailureClassification.PATCH_APPLICATION_FAILED

    # Regression test failed
    verdict, failure = determine_double_validation_verdict(
        patch_applied=True,
        patch_classification=None,
        regression_passed=False,
        regression_classification=VerificationFailureClassification.REGRESSION_STILL_FAILING,
        baseline_passed=False,
        baseline_classification=None,
        source_integrity_intact=True,
    )
    assert verdict == PatchVerificationVerdict.UNVERIFIED
    assert failure == VerificationFailureClassification.REGRESSION_STILL_FAILING

    # Baseline suite failed
    verdict, failure = determine_double_validation_verdict(
        patch_applied=True,
        patch_classification=None,
        regression_passed=True,
        regression_classification=None,
        baseline_passed=False,
        baseline_classification=VerificationFailureClassification.BASELINE_TEST_FAILURE,
        source_integrity_intact=True,
    )
    assert verdict == PatchVerificationVerdict.UNVERIFIED
    assert failure == VerificationFailureClassification.BASELINE_TEST_FAILURE

    # Source integrity violated
    verdict, failure = determine_double_validation_verdict(
        patch_applied=True,
        patch_classification=None,
        regression_passed=True,
        regression_classification=None,
        baseline_passed=True,
        baseline_classification=None,
        source_integrity_intact=False,
    )
    assert verdict == PatchVerificationVerdict.UNVERIFIED
    assert failure == VerificationFailureClassification.SOURCE_INTEGRITY_VIOLATION
