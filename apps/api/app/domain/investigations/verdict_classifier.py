"""Deterministic Verdict Classifier for Regression Test Verification

Distinguishes genuine defect assertion failures from test execution errors,
import errors, collection failures, timeouts, and passing test rejections.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.investigations.models import (
    RegressionFailureClassification,
    RegressionVerificationStatus,
)


@dataclass(frozen=True)
class ClassifiedVerdict:
    status: RegressionVerificationStatus
    failure_classification: RegressionFailureClassification
    summary: str


# Regexes detecting syntax / import / collection failures that must NOT be counted as regression proof
EXECUTION_ERROR_PATTERNS = [
    re.compile(r"ERROR\s+collecting\s+", re.MULTILINE),
    re.compile(r"ImportError:\s+", re.MULTILINE),
    re.compile(r"ModuleNotFoundError:\s+", re.MULTILINE),
    re.compile(r"SyntaxError:\s+", re.MULTILINE),
    re.compile(r"IndentationError:\s+", re.MULTILINE),
    re.compile(r"INTERNALERROR>", re.MULTILINE),
    re.compile(r"NameError:\s+name\s+'.+'\s+is\s+not\s+defined", re.MULTILINE),
]

# Regexes detecting genuine test failure assertions
ASSERTION_FAILURE_PATTERNS = [
    re.compile(r"FAILED\s+[^\s:]+::test_[a-zA-Z0-9_]+", re.MULTILINE),
    re.compile(r"AssertionError", re.MULTILINE),
    re.compile(r"assert\s+.+", re.MULTILINE),
]


def classify_regression_test_verdict(
    exit_code: int | None,
    stdout: str,
    stderr: str,
    timed_out: bool = False,
    policy_blocked: bool = False,
) -> ClassifiedVerdict:
    """Deterministically classify the result of executing a regression test.

    Invariant:
        Only an executed test whose assertions fail against the buggy codebase
        receives REGRESSION_PROVEN.
        All other failures (syntax, imports, timeouts, sandbox errors) receive
        EXECUTION_ERROR or TIMEOUT and are never treated as proof.
    """
    if policy_blocked:
        return ClassifiedVerdict(
            status=RegressionVerificationStatus.POLICY_BLOCKED,
            failure_classification=RegressionFailureClassification.POLICY_BLOCKED,
            summary="Command or test violated sandbox security policy.",
        )

    if timed_out:
        return ClassifiedVerdict(
            status=RegressionVerificationStatus.TIMEOUT,
            failure_classification=RegressionFailureClassification.TIMEOUT,
            summary="Regression test execution exceeded wall-clock timeout.",
        )

    if exit_code is None:
        return ClassifiedVerdict(
            status=RegressionVerificationStatus.EXECUTION_ERROR,
            failure_classification=RegressionFailureClassification.TEST_EXECUTION_ERROR,
            summary="Process terminated without reporting an exit code.",
        )

    # 1. Exit code 0 means test passed (did not catch the bug)
    if exit_code == 0:
        return ClassifiedVerdict(
            status=RegressionVerificationStatus.TEST_REJECTED,
            failure_classification=RegressionFailureClassification.PASSING,
            summary="Test passed against the buggy repository; defect was not demonstrated.",
        )

    # 2. Check for infrastructure, import, collection, or syntax errors first
    combined_output = f"{stdout}\n{stderr}"
    for pat in EXECUTION_ERROR_PATTERNS:
        match = pat.search(combined_output)
        if match:
            return ClassifiedVerdict(
                status=RegressionVerificationStatus.EXECUTION_ERROR,
                failure_classification=RegressionFailureClassification.TEST_EXECUTION_ERROR,
                summary=f"Test failed during execution/import/collection: {match.group(0).strip()}",
            )

    # Pytest exit code 2: Interrupted / syntax error during collection
    # Pytest exit code 4: Usage error (file not found / bad flags)
    # Pytest exit code 5: No tests collected
    if exit_code in (2, 3, 4, 5):
        return ClassifiedVerdict(
            status=RegressionVerificationStatus.EXECUTION_ERROR,
            failure_classification=RegressionFailureClassification.TEST_EXECUTION_ERROR,
            summary=f"Pytest reported execution error with exit code {exit_code}.",
        )

    # 3. Check for genuine test assertion failure
    has_failed_test = any(pat.search(combined_output) for pat in ASSERTION_FAILURE_PATTERNS)
    if exit_code == 1 and has_failed_test:
        return ClassifiedVerdict(
            status=RegressionVerificationStatus.REGRESSION_PROVEN,
            failure_classification=RegressionFailureClassification.ASSERTION_FAILURE,
            summary="Regression test executed and failed on expected assertion: defect proven.",
        )

    # Fallback to execution error if non-zero exit code cannot be positively confirmed as assertion failure
    return ClassifiedVerdict(
        status=RegressionVerificationStatus.EXECUTION_ERROR,
        failure_classification=RegressionFailureClassification.TEST_EXECUTION_ERROR,
        summary=f"Non-zero exit code {exit_code} without verified assertion failure.",
    )
