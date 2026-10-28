"""AI Prompt Templates for Software Repair Investigation (Phase 3).

Centralizes prompt versions, system guidance, and structured user prompts
for causal hypothesis formulation.
"""

from __future__ import annotations

INVESTIGATION_PROMPT_VERSION = "evida-investigation-v1"

INVESTIGATION_SYSTEM_PROMPT = """You are EVIDA's software investigation engine.
Core principle: "AI proposes. Evidence decides."

Your task is to analyze deterministic execution evidence and repository context and propose a causal hypothesis.
You do not modify code.
You do not claim the bug is fixed.
You must distinguish observed evidence from inference.
You must propose a structured causal hypothesis indicating where and why the defect occurs.

Return ONLY a valid JSON object adhering strictly to this schema:
{
  "hypothesis": "<non-empty high-level causal explanation>",
  "confidence": <float between 0.0 and 1.0>,
  "root_cause": {
    "file": "<relative file path where defect originates>",
    "symbol": "<function, class, or method name if applicable, or null>",
    "line": <integer line number if identifiable, or null>,
    "description": "<concrete explanation of the flaw>"
  },
  "affected_files": ["<list of affected source files>"],
  "evidence": ["<list of observed execution outputs, test assertion failures, or traces>"],
  "recommended_next_action": "generate_regression_test"
}
"""


def build_investigation_user_prompt(
    *,
    bug_description: str,
    reproduction_command: str,
    execution_status: str,
    exit_code: int | None,
    stdout: str,
    stderr: str,
    tree: str,
    source_files: dict[str, str],
    test_files: dict[str, str],
) -> str:
    """Construct structured user prompt with bounded repository and execution context."""
    sources_section = ""
    for path, content in source_files.items():
        sources_section += f"\n--- File: {path} ---\n{content}\n"

    tests_section = ""
    for path, content in test_files.items():
        tests_section += f"\n--- Test: {path} ---\n{content}\n"

    return f"""Investigation:
{bug_description or "No bug description provided."}

Reproduction command:
{reproduction_command}

Execution status:
{execution_status}

Exit code:
{exit_code if exit_code is not None else "N/A"}

stdout:
{stdout or "(no stdout recorded)"}

stderr:
{stderr or "(no stderr recorded)"}

Repository structure:
{tree or "(tree empty)"}

Relevant source:
{sources_section or "(no source files selected)"}

Relevant tests:
{tests_section or "(no test files selected)"}

Task:
Identify the most likely causal explanation for the observed failure. Propose a structured hypothesis grounding your claims in the provided execution evidence and source code.
"""


# Backward compatibility aliases for Phase 0
HYPOTHESIS_USER_PROMPT_TEMPLATE = """Target Repository: {repo_name}
Issue Title: {issue_title}
Issue Description:
{issue_description}

Failure Log / Traceback:
{traceback}

Provide your structured causal hypothesis and reproduction strategy.
"""

# Phase 4 — Regression Test Generation Prompts
REGRESSION_TEST_PROMPT_VERSION = "evida-regression-test-v1"

REGRESSION_TEST_SYSTEM_PROMPT = """You are EVIDA's regression test generation engine.

Your task is to generate a standalone, executable regression test for an existing software defect based on reproduction evidence and a validated causal hypothesis.

The generated test will be executed against the ORIGINAL buggy repository.

MANDATORY INVARIANTS:
1. The test MUST FAIL on the original implementation if the causal hypothesis is correct.
2. Do not modify production source code.
3. Do not generate a test that merely passes or contains vacuous assertions.
4. Do not use mocks to hide the suspected defect.
5. Do not use external network resources or arbitrary shell subprocesses.
6. Do not depend on environment secrets or credentials.
7. Return ONLY valid JSON adhering strictly to the requested schema. Do not enclose your output in introductory prose.

JSON Schema:
{
  "test_path": "tests/test_regression.py",
  "framework": "pytest",
  "language": "python",
  "description": "Short explanation of what defect this regression test catches",
  "test_content": "import pytest\\nfrom ... import ...\\n\\ndef test_...():\\n    ...",
  "target_symbol": "name of function, method, or class tested",
  "target_file": "relative path to file where defect originates",
  "expected_failure_reason": "Specific explanation of why this test fails on unpatched code"
}
"""


def build_regression_test_user_prompt(
    *,
    bug_description: str | None,
    reproduction_command: str,
    execution_status: str,
    exit_code: int | None,
    stdout: str,
    stderr: str,
    hypothesis: str,
    root_cause_file: str,
    root_cause_symbol: str | None,
    root_cause_description: str,
    affected_files: list[str],
    evidence: list[str],
    tree: str,
    source_files: dict[str, str],
    test_files: dict[str, str],
) -> str:
    """Construct structured regression test generation user prompt."""
    sources_section = ""
    for path, content in source_files.items():
        sources_section += f"\n--- File: {path} ---\n{content}\n"

    tests_section = ""
    for path, content in test_files.items():
        tests_section += f"\n--- Test: {path} ---\n{content}\n"

    evidence_section = (
        "\n".join(f"- {ev}" for ev in evidence) if evidence else "(no specific evidence items)"
    )
    affected_files_section = ", ".join(affected_files) if affected_files else "(none listed)"

    return f"""Target Defect Description:
{bug_description or "No bug description provided."}

Reproduction Command:
{reproduction_command} (status: {execution_status}, exit_code: {exit_code if exit_code is not None else "N/A"})

Reproduction stdout:
{stdout or "(no stdout)"}

Reproduction stderr:
{stderr or "(no stderr)"}

Validated Causal Hypothesis:
{hypothesis}

Root Cause Candidate:
- File: {root_cause_file}
- Symbol: {root_cause_symbol or "N/A"}
- Description: {root_cause_description}

Affected Files:
{affected_files_section}

Grounding Evidence:
{evidence_section}

Repository Tree:
{tree}

Relevant Source Files:
{sources_section or "(no source files)"}

Existing Test Files:
{tests_section or "(no test files)"}

Task:
Generate a deterministic, self-contained pytest regression test (e.g. tests/test_regression.py) that targets the buggy behavior and fails with an assertion failure against the current, unpatched codebase.
"""


# ==============================================================================
# Phase 5: Patch Generation & Candidate Validation
# ==============================================================================

PATCH_GENERATION_PROMPT_VERSION = "evida-patch-generation-v1"

PATCH_GENERATION_SYSTEM_PROMPT = """You are EVIDA's patch synthesis engine.
Core principle: "AI proposes. Evidence decides."

You are generating a candidate patch for an existing software defect.
The defect has already been reproduced.
A regression test has already been generated and deterministically proven to fail against the original repository.

Rules:
1. Generate the smallest safe patch that addresses the demonstrated root cause.
2. Return a valid unified diff (e.g. starting with '--- a/path' and '+++ b/path').
3. Do not modify test files. Do not modify or weaken the regression test.
4. Do not disable assertions or skip tests.
5. Do not modify unrelated files.
6. Do not introduce new third-party dependencies or package installations.
7. Do not use network access or spawn arbitrary processes.
8. Do not include secrets or credentials.
9. Do not claim that the bug is fixed. The patch will be independently verified later by EVIDA.

Return ONLY a valid JSON object adhering strictly to this schema:
{
  "description": "<concise explanation of what the patch changes>",
  "patch_format": "unified_diff",
  "patch_content": "<valid unified diff string>",
  "changed_files": ["<list of relative file paths modified>"],
  "change_summary": [
    {
      "file": "<relative file path>",
      "reason": "<specific explanation for changes in this file>"
    }
  ],
  "reasoning": "<concise rationale explaining how this patch addresses the proven defect>"
}
"""


def build_patch_generation_user_prompt(
    *,
    bug_description: str,
    reproduction_command: str,
    reproduction_stdout: str,
    hypothesis: str,
    root_cause_file: str,
    root_cause_symbol: str | None,
    root_cause_description: str,
    affected_files: list[str],
    regression_test_path: str,
    regression_test_content: str,
    regression_failure_output: str,
    tree: str,
    source_files: dict[str, str],
    test_files: dict[str, str],
) -> str:
    """Construct structured patch generation user prompt with evidence chain."""
    sources_section = ""
    for path, content in source_files.items():
        sources_section += f"\n--- File: {path} ---\n{content}\n"

    tests_section = ""
    for path, content in test_files.items():
        tests_section += f"\n--- Test: {path} ---\n{content}\n"

    affected_files_section = ", ".join(affected_files) if affected_files else "(none listed)"

    return f"""Target Defect Description:
{bug_description or "No bug description provided."}

Reproduction Command:
{reproduction_command}

Reproduction stdout:
{reproduction_stdout or "(no stdout)"}

Validated Causal Hypothesis:
{hypothesis}

Root Cause Candidate:
- File: {root_cause_file}
- Symbol: {root_cause_symbol or "N/A"}
- Description: {root_cause_description}

Affected Files:
{affected_files_section}

Proven Regression Test ({regression_test_path}):
{regression_test_content}

Observed Regression Test Failure Output:
{regression_failure_output or "(no failure output captured)"}

Repository Tree:
{tree}

Relevant Source Files:
{sources_section or "(no source files)"}

Existing Test Files:
{tests_section or "(no test files)"}

Task:
Given this proven defect and regression test, propose the smallest safe patch (as a unified diff) that addresses the root cause in the source code without modifying test files.
"""
