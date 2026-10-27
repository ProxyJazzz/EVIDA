"""Unit tests for AI Investigation, Prompt Generation, and Hypothesis Validation (Phase 3)."""

from uuid import uuid4

import pytest
from app.ai.prompts import (
    INVESTIGATION_PROMPT_VERSION,
    INVESTIGATION_SYSTEM_PROMPT,
    build_investigation_user_prompt,
)
from app.domain.investigations.ai_service import extract_json_payload
from app.domain.investigations.models import (
    InvestigationHypothesis,
    InvestigationHypothesisRecord,
    RootCauseCandidate,
)
from pydantic import ValidationError


def test_prompt_version_and_system_prompt() -> None:
    assert INVESTIGATION_PROMPT_VERSION == "evida-investigation-v1"
    assert "AI proposes. Evidence decides." in INVESTIGATION_SYSTEM_PROMPT
    assert "You do not modify code" in INVESTIGATION_SYSTEM_PROMPT
    assert (
        "InvestigationHypothesis" in INVESTIGATION_SYSTEM_PROMPT
        or "schema" in INVESTIGATION_SYSTEM_PROMPT
    )


def test_build_investigation_user_prompt() -> None:
    prompt = build_investigation_user_prompt(
        bug_description="divide(10, 2) returns 20 instead of 5.",
        reproduction_command="pytest tests/test_bug.py",
        execution_status="REPRODUCED",
        exit_code=1,
        stdout="FAILED tests/test_bug.py::test_divide_bug",
        stderr="",
        tree="📁 src/\n  📄 calculator.py",
        source_files={"src/calculator.py": "def divide(a, b): return a * b\n"},
        test_files={
            "tests/test_bug.py": "def test_divide_bug(): assert divide(10, 2) == 5\n"
        },
    )
    assert "divide(10, 2) returns 20 instead of 5." in prompt
    assert "pytest tests/test_bug.py" in prompt
    assert "REPRODUCED" in prompt
    assert "src/calculator.py" in prompt
    assert "def divide(a, b): return a * b" in prompt


def test_extract_json_payload_markdown_fences() -> None:
    fenced_json = """
Here is my analysis:
```json
{
  "hypothesis": "Division logic defect",
  "confidence": 0.95,
  "root_cause": {
    "file": "src/calculator.py",
    "symbol": "divide",
    "line": 4,
    "description": "Multiplication operator used."
  },
  "affected_files": ["src/calculator.py"],
  "evidence": ["AssertionError 20 != 5"],
  "recommended_next_action": "generate_regression_test"
}
```
Hope this helps!
"""
    extracted = extract_json_payload(fenced_json)
    assert extracted.startswith("{")
    assert extracted.endswith("}")
    assert '"hypothesis": "Division logic defect"' in extracted


def test_extract_json_payload_raw() -> None:
    raw = '{"hypothesis": "Test", "confidence": 0.9, "root_cause": {"file": "a.py", "description": "b"}}'
    assert extract_json_payload(raw) == raw


def test_hypothesis_validation_success() -> None:
    hypo = InvestigationHypothesis(
        hypothesis="Multiplication instead of division",
        confidence=0.98,
        root_cause=RootCauseCandidate(
            file="src/calculator.py",
            symbol="divide",
            line=4,
            description="Uses * instead of /",
        ),
        affected_files=["src/calculator.py"],
        evidence=["Exit code 1 from pytest"],
        recommended_next_action="generate_regression_test",
    )
    assert hypo.confidence == 0.98
    assert hypo.root_cause.file == "src/calculator.py"
    assert hypo.summary == "Multiplication instead of division"  # backward compat


def test_hypothesis_validation_confidence_bounds() -> None:
    # Confidence > 1.0 must fail
    with pytest.raises(ValidationError):
        InvestigationHypothesis(
            hypothesis="Too confident",
            confidence=1.5,
            root_cause=RootCauseCandidate(file="a.py", description="err"),
        )

    # Confidence < 0.0 must fail
    with pytest.raises(ValidationError):
        InvestigationHypothesis(
            hypothesis="Negative confidence",
            confidence=-0.1,
            root_cause=RootCauseCandidate(file="a.py", description="err"),
        )


def test_hypothesis_record_creation() -> None:
    inv_id = uuid4()
    run_id = uuid4()
    record = InvestigationHypothesisRecord(
        investigation_id=inv_id,
        reproduction_run_id=run_id,
        model="nvidia/Nemotron-3_5-Lightning",
        provider="nebius",
        hypothesis="Defect in calculator",
        confidence=0.92,
        root_cause=RootCauseCandidate(file="src/calculator.py", description="Bad math"),
        affected_files=["src/calculator.py"],
        evidence=["AssertionError: assert 20 == 5"],
        input_tokens=150,
        output_tokens=60,
        latency_ms=320,
    )
    assert record.investigation_id == inv_id
    assert record.reproduction_run_id == run_id
    assert record.prompt_version == "evida-investigation-v1"
    assert record.confidence == 0.92
