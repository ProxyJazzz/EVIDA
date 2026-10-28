"""Unit tests for Phase 5 Patch Proposal Schema and Prompt Construction."""

from __future__ import annotations

import pytest
from app.ai.prompts import (
    PATCH_GENERATION_PROMPT_VERSION,
    PATCH_GENERATION_SYSTEM_PROMPT,
    build_patch_generation_user_prompt,
)
from app.domain.patches.models import (
    ChangeSummaryItem,
    PatchProposal,
)
from pydantic import ValidationError


def test_valid_patch_proposal():
    proposal = PatchProposal(
        description="Fix calculator division operator.",
        patch_format="unified_diff",
        patch_content="--- a/src/calculator.py\n+++ b/src/calculator.py\n@@ -1,2 +1,2 @@\n- return a * b\n+ return a / b\n",
        changed_files=["src/calculator.py"],
        change_summary=[
            ChangeSummaryItem(file="src/calculator.py", reason="Replace * with /")
        ],
        reasoning="Multiplication was used instead of division.",
    )
    assert proposal.description == "Fix calculator division operator."
    assert proposal.patch_format == "unified_diff"
    assert proposal.changed_files == ["src/calculator.py"]


def test_patch_proposal_missing_fields():
    with pytest.raises(ValidationError):
        PatchProposal.model_validate(
            {
                "description": "Missing content",
                "patch_format": "unified_diff",
            }
        )


def test_patch_proposal_invalid_format():
    with pytest.raises(ValidationError):
        PatchProposal.model_validate(
            {
                "description": "Invalid format",
                "patch_format": "git_diff",  # Must be 'unified_diff'
                "patch_content": "some diff",
                "changed_files": ["src/calc.py"],
                "reasoning": "some reason",
            }
        )


def test_patch_proposal_empty_changed_files():
    with pytest.raises(ValidationError):
        PatchProposal.model_validate(
            {
                "description": "Empty files",
                "patch_format": "unified_diff",
                "patch_content": "diff",
                "changed_files": [],  # Min length 1
                "reasoning": "some reason",
            }
        )


def test_patch_prompt_version_and_system_prompt():
    assert PATCH_GENERATION_PROMPT_VERSION == "evida-patch-generation-v1"
    assert "patch synthesis engine" in PATCH_GENERATION_SYSTEM_PROMPT
    assert "Do not modify test files" in PATCH_GENERATION_SYSTEM_PROMPT
    assert "Do not claim that the bug is fixed" in PATCH_GENERATION_SYSTEM_PROMPT
    assert "unified_diff" in PATCH_GENERATION_SYSTEM_PROMPT


def test_build_patch_generation_user_prompt():
    prompt = build_patch_generation_user_prompt(
        bug_description="divide(10, 2) returns 20 instead of 5.",
        reproduction_command="pytest tests/test_bug.py",
        reproduction_stdout="FAILED tests/test_bug.py - assert 20 == 5",
        hypothesis="divide() uses multiplication instead of division.",
        root_cause_file="src/calculator.py",
        root_cause_symbol="divide",
        root_cause_description="Uses * operator",
        affected_files=["src/calculator.py"],
        regression_test_path="tests/test_regression.py",
        regression_test_content="def test_divide(): assert divide(10, 2) == 5",
        regression_failure_output="assert 20 == 5",
        tree="src/\n  calculator.py",
        source_files={"src/calculator.py": "def divide(a, b): return a * b"},
        test_files={"tests/test_bug.py": "assert divide(10, 2) == 5"},
    )

    assert "divide(10, 2) returns 20 instead of 5." in prompt
    assert "pytest tests/test_bug.py" in prompt
    assert "divide() uses multiplication instead of division." in prompt
    assert "src/calculator.py" in prompt
    assert "tests/test_regression.py" in prompt
    assert "def test_divide(): assert divide(10, 2) == 5" in prompt
    assert "assert 20 == 5" in prompt
    assert "src/calculator.py" in prompt
    assert "def divide(a, b): return a * b" in prompt
    assert "propose the smallest safe patch" in prompt
