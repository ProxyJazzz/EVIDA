"""Unit Tests for Reproduction Command Validation (Phase 2)."""

import pytest
from app.domain.investigations.state_machine import LifecycleException
from app.domain.repositories.command_validator import validate_reproduction_command


def test_validate_allowed_pytest_commands() -> None:
    assert validate_reproduction_command("pytest") == ["pytest"]
    assert validate_reproduction_command("pytest tests/test_bug.py") == [
        "pytest",
        "tests/test_bug.py",
    ]
    assert validate_reproduction_command("pytest -q tests/test_reproduce.py") == [
        "pytest",
        "-q",
        "tests/test_reproduce.py",
    ]


def test_validate_allowed_python_commands() -> None:
    assert validate_reproduction_command("python -m pytest tests/test_bug.py") == [
        "python",
        "-m",
        "pytest",
        "tests/test_bug.py",
    ]
    assert validate_reproduction_command("python tests/reproduce.py") == [
        "python",
        "tests/reproduce.py",
    ]
    assert validate_reproduction_command("python3 -m unittest tests/test_bug.py") == [
        "python3",
        "-m",
        "unittest",
        "tests/test_bug.py",
    ]


def test_reject_empty_or_whitespace_command() -> None:
    with pytest.raises(LifecycleException) as exc_info:
        validate_reproduction_command("")
    assert exc_info.value.code == "INVALID_REPRODUCTION_COMMAND"

    with pytest.raises(LifecycleException) as exc_info:
        validate_reproduction_command("   ")
    assert exc_info.value.code == "INVALID_REPRODUCTION_COMMAND"


@pytest.mark.parametrize(
    "char",
    [";", "&", "|", "`", "$", "(", ")", "{", "}", "<", ">", "\n"],
)
def test_reject_shell_metacharacters(char: str) -> None:
    with pytest.raises(LifecycleException) as exc_info:
        validate_reproduction_command(f"pytest {char} echo evil")
    assert exc_info.value.code in {
        "INVALID_REPRODUCTION_COMMAND",
        "EXECUTION_POLICY_BLOCKED",
    }
    assert "shell" in exc_info.value.message.lower()


def test_reject_disallowed_executables() -> None:
    for cmd in ["rm -rf /", "bash -c 'echo hi'", "sh run.sh", "curl http://evil.com"]:
        with pytest.raises(LifecycleException) as exc_info:
            validate_reproduction_command(cmd)
        assert exc_info.value.code in {
            "INVALID_REPRODUCTION_COMMAND",
            "EXECUTION_POLICY_BLOCKED",
        }


def test_reject_inline_python_execution() -> None:
    with pytest.raises(LifecycleException) as exc_info:
        validate_reproduction_command("python -c quit")
    assert exc_info.value.code in {
        "INVALID_REPRODUCTION_COMMAND",
        "EXECUTION_POLICY_BLOCKED",
    }
    assert "inline" in exc_info.value.message.lower()


def test_reject_directory_traversal_in_arguments() -> None:
    with pytest.raises(LifecycleException) as exc_info:
        validate_reproduction_command("pytest ../../../etc/passwd")
    assert exc_info.value.code in {
        "INVALID_REPRODUCTION_COMMAND",
        "EXECUTION_POLICY_BLOCKED",
    }
    assert "traversal" in exc_info.value.message.lower()
