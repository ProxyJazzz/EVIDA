"""Unit tests for Phase 4 Regression Test Schema, Proposal Model, and Prompt Construction."""

from __future__ import annotations

import pytest
from app.ai.prompts import (
    REGRESSION_TEST_PROMPT_VERSION,
    REGRESSION_TEST_SYSTEM_PROMPT,
    build_regression_test_user_prompt,
)
from app.domain.investigations.models import (
    InvestigationRegressionTestRecord,
    RegressionTestGenerationStatus,
    RegressionTestProposal,
    RegressionVerificationStatus,
)
from pydantic import ValidationError


def test_regression_test_proposal_valid() -> None:
    """Valid proposal model creates successfully."""
    proposal = RegressionTestProposal(
        test_path="tests/test_regression.py",
        framework="pytest",
        language="python",
        description="Verifies divide function handles division correctly.",
        test_content="def test_divide(): assert True",
        target_symbol="divide",
        target_file="src/calculator.py",
        expected_failure_reason="Multiplies instead of divides.",
    )
    assert proposal.test_path == "tests/test_regression.py"
    assert proposal.framework == "pytest"
    assert proposal.target_symbol == "divide"


def test_regression_test_proposal_missing_fields() -> None:
    """Missing required fields raises ValidationError."""
    with pytest.raises(ValidationError):
        RegressionTestProposal(
            test_path="tests/test_regression.py",
            # missing description, test_content, target_symbol, etc.
        )  # type: ignore[call-arg]


def test_regression_test_record_defaults() -> None:
    """Record model sets proper defaults and enums."""
    from uuid import uuid4

    record = InvestigationRegressionTestRecord(
        investigation_id=uuid4(),
        hypothesis_id=uuid4(),
        test_path="tests/test_regression.py",
        test_content="def test_foo(): pass",
        description="Regression test description",
    )
    assert record.status == RegressionTestGenerationStatus.GENERATED
    assert record.verification_status == RegressionVerificationStatus.PENDING
    assert record.prompt_version == REGRESSION_TEST_PROMPT_VERSION
    assert record.framework == "pytest"


def test_regression_prompt_structure() -> None:
    """Regression test system and user prompts include required invariants and sections."""
    assert REGRESSION_TEST_PROMPT_VERSION == "evida-regression-test-v1"
    assert (
        "The test MUST FAIL on the original implementation"
        in REGRESSION_TEST_SYSTEM_PROMPT
    )
    assert "Do not modify production source code" in REGRESSION_TEST_SYSTEM_PROMPT

    user_prompt = build_regression_test_user_prompt(
        bug_description="divide(10, 2) returns 20",
        reproduction_command="pytest tests/test_bug.py",
        execution_status="REPRODUCED",
        exit_code=1,
        stdout="FAILED tests/test_bug.py",
        stderr="",
        hypothesis="Function multiplies instead of divides",
        root_cause_file="src/calculator.py",
        root_cause_symbol="divide",
        root_cause_description="Uses * operator",
        affected_files=["src/calculator.py"],
        evidence=["AssertionError: assert 20 == 5"],
        tree="src/\n  calculator.py\ntests/\n  test_bug.py",
        source_files={"src/calculator.py": "def divide(a, b): return a * b\n"},
        test_files={"tests/test_bug.py": "def test_bug(): pass\n"},
    )
    assert "divide(10, 2) returns 20" in user_prompt
    assert "pytest tests/test_bug.py" in user_prompt
    assert "src/calculator.py" in user_prompt
    assert "Function multiplies instead of divides" in user_prompt
    assert "def divide(a, b): return a * b" in user_prompt
