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
