"""Unit tests for Phase 4 Deterministic Verdict Classifier."""

from __future__ import annotations

from app.domain.investigations.models import (
    RegressionFailureClassification,
    RegressionVerificationStatus,
)
from app.domain.investigations.verdict_classifier import (
    classify_regression_test_verdict,
)


def test_classify_assertion_failure_proves_regression() -> None:
    """Exit code 1 with genuine assertion failure yields REGRESSION_PROVEN."""
    stdout = """
============================= test session starts ==============================
FAILED tests/test_regression.py::test_divide_regression - assert 20 == 5
============================== 1 failed in 0.12s ===============================
"""
    verdict = classify_regression_test_verdict(
        exit_code=1,
        stdout=stdout,
        stderr="",
        timed_out=False,
    )
    assert verdict.status == RegressionVerificationStatus.REGRESSION_PROVEN
    assert (
        verdict.failure_classification
        == RegressionFailureClassification.ASSERTION_FAILURE
    )


def test_classify_passing_test_rejected() -> None:
    """Exit code 0 means the test passed and failed to demonstrate the defect."""
    stdout = """
============================= test session starts ==============================
1 passed in 0.05s
"""
    verdict = classify_regression_test_verdict(
        exit_code=0,
        stdout=stdout,
        stderr="",
        timed_out=False,
    )
    assert verdict.status == RegressionVerificationStatus.TEST_REJECTED
    assert verdict.failure_classification == RegressionFailureClassification.PASSING


def test_classify_timeout() -> None:
    """Execution timeout yields TIMEOUT and is never proven."""
    verdict = classify_regression_test_verdict(
        exit_code=-9,
        stdout="",
        stderr="Process killed after 30s",
        timed_out=True,
    )
    assert verdict.status == RegressionVerificationStatus.TIMEOUT
    assert verdict.failure_classification == RegressionFailureClassification.TIMEOUT


def test_classify_import_error_is_execution_error() -> None:
    """Import error in test is an EXECUTION_ERROR, never REGRESSION_PROVEN."""
    stdout = """
ImportError: cannot import name 'foo' from 'src.calculator'
"""
    verdict = classify_regression_test_verdict(
        exit_code=1,
        stdout=stdout,
        stderr="",
        timed_out=False,
    )
    assert verdict.status == RegressionVerificationStatus.EXECUTION_ERROR
    assert (
        verdict.failure_classification
        == RegressionFailureClassification.TEST_EXECUTION_ERROR
    )


def test_classify_module_not_found_is_execution_error() -> None:
    """ModuleNotFoundError is an EXECUTION_ERROR, never REGRESSION_PROVEN."""
    stderr = """
ModuleNotFoundError: No module named 'nonexistent_package'
"""
    verdict = classify_regression_test_verdict(
        exit_code=2,
        stdout="",
        stderr=stderr,
        timed_out=False,
    )
    assert verdict.status == RegressionVerificationStatus.EXECUTION_ERROR
    assert (
        verdict.failure_classification
        == RegressionFailureClassification.TEST_EXECUTION_ERROR
    )


def test_classify_collection_error_is_execution_error() -> None:
    """Pytest collection failure is an EXECUTION_ERROR."""
    stdout = """
ERROR collecting tests/test_regression.py
"""
    verdict = classify_regression_test_verdict(
        exit_code=2,
        stdout=stdout,
        stderr="",
        timed_out=False,
    )
    assert verdict.status == RegressionVerificationStatus.EXECUTION_ERROR
    assert (
        verdict.failure_classification
        == RegressionFailureClassification.TEST_EXECUTION_ERROR
    )


def test_classify_policy_blocked() -> None:
    """Policy violation yields POLICY_BLOCKED."""
    verdict = classify_regression_test_verdict(
        exit_code=None,
        stdout="",
        stderr="Command violates security policy",
        policy_blocked=True,
    )
    assert verdict.status == RegressionVerificationStatus.POLICY_BLOCKED
    assert (
        verdict.failure_classification == RegressionFailureClassification.POLICY_BLOCKED
    )
