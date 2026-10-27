"""Unit tests for Phase 4 Regression Test Validator and AST Safety Checks."""

from __future__ import annotations

import pytest
from app.domain.investigations.test_validator import (
    RegressionTestValidationError,
    validate_regression_test_content,
    validate_regression_test_proposal,
    validate_test_path,
)


def test_validate_valid_test_path() -> None:
    """Valid relative test paths are accepted."""
    validate_test_path("tests/test_regression.py")
    validate_test_path("tests/sub/test_math.py")
    validate_test_path("test_calculator.py")


@pytest.mark.parametrize(
    "invalid_path",
    [
        "/tests/test_foo.py",
        "\\tests\\test_foo.py",
        "../test_foo.py",
        "tests/../../test_foo.py",
        "tests/test_foo.txt",
        "tests/calculator.py",
        "tests/test_foo.py\0",
        "",
        "   ",
    ],
)
def test_validate_invalid_test_path(invalid_path: str) -> None:
    """Unsafe or invalid test paths are rejected."""
    with pytest.raises(RegressionTestValidationError):
        validate_test_path(invalid_path)


def test_validate_valid_test_content() -> None:
    """Valid test content with proper pytest structure is accepted."""
    code = """
from src.calculator import divide

def test_divide_regression():
    assert divide(10, 2) == 5
"""
    validate_regression_test_content(code, max_bytes=20000)


def test_validate_empty_test_content() -> None:
    """Empty or whitespace-only test content is rejected."""
    with pytest.raises(RegressionTestValidationError) as exc:
        validate_regression_test_content("", max_bytes=20000)
    assert exc.value.code == "REGRESSION_CONTENT_EMPTY"


def test_validate_oversized_test_content() -> None:
    """Test content exceeding max byte limit is rejected."""
    code = "def test_foo(): pass\n" + "#" * 1000
    with pytest.raises(RegressionTestValidationError) as exc:
        validate_regression_test_content(code, max_bytes=500)
    assert exc.value.code == "REGRESSION_CONTENT_TOO_LARGE"


def test_validate_syntax_error_in_test_content() -> None:
    """Invalid Python syntax is rejected with syntax error code."""
    code = "def test_broken(:\n    assert True"
    with pytest.raises(RegressionTestValidationError) as exc:
        validate_regression_test_content(code, max_bytes=20000)
    assert exc.value.code == "REGRESSION_SYNTAX_ERROR"


def test_validate_missing_test_function() -> None:
    """Test content without any test_ function or Test class is rejected."""
    code = """
def helper_function():
    return 42

x = helper_function()
"""
    with pytest.raises(RegressionTestValidationError) as exc:
        validate_regression_test_content(code, max_bytes=20000)
    assert exc.value.code == "REGRESSION_STRUCTURE_INVALID"


@pytest.mark.parametrize(
    "dangerous_code",
    [
        "import subprocess\ndef test_attack(): subprocess.run(['ls'])",
        "import socket\ndef test_net(): s = socket.socket()",
        "import requests\ndef test_net(): requests.get('https://evil.com')",
        "import urllib.request\ndef test_net(): urllib.request.urlopen('http://evil.com')",
        "from os import system\ndef test_sys(): system('rm -rf /')",
        "import os\ndef test_sys(): os.system('cat /etc/passwd')",
        "import os\ndef test_sys(): os.popen('whoami')",
        "import shutil\ndef test_del(): shutil.rmtree('/tmp/safe')",
        'def test_eval(): eval(\'__import__("os").system("id")\')',
        "def test_exec(): exec('import os')",
        "def test_write():\n    with open('src/calculator.py', 'w') as f: f.write('evil')",
    ],
)
def test_validate_dangerous_ast_nodes_rejected(dangerous_code: str) -> None:
    """Dangerous imports, subprocess execution, file overwriting, and eval are rejected."""
    with pytest.raises(RegressionTestValidationError) as exc:
        validate_regression_test_content(dangerous_code, max_bytes=20000)
    assert exc.value.code == "REGRESSION_SECURITY_VIOLATION"


def test_validate_regression_test_proposal_complete() -> None:
    """End-to-end proposal validation accepts clean proposals."""
    validate_regression_test_proposal(
        test_path="tests/test_regression.py",
        test_content="def test_regression(): assert True",
        max_bytes=20000,
    )
