"""Unit tests for Repository Context Builder and Stack Trace Extraction (Phase 3)."""

import tempfile
from pathlib import Path

import pytest
from app.core.config import Settings
from app.domain.investigations.context_builder import (
    build_investigation_context,
    build_repository_tree,
    extract_stack_trace_hints,
    is_sensitive_file,
)
from app.domain.investigations.state_machine import LifecycleException


def test_sensitive_file_detection() -> None:
    assert is_sensitive_file(".env") is True
    assert is_sensitive_file(".env.local") is True
    assert is_sensitive_file(".env.production") is True
    assert is_sensitive_file("server.key") is True
    assert is_sensitive_file("cert.pem") is True
    assert is_sensitive_file("credentials.json") is True
    assert is_sensitive_file("service-account-prod.json") is True
    assert is_sensitive_file("id_rsa") is True
    assert is_sensitive_file("user_secret_token.txt") is True

    # Safe files
    assert is_sensitive_file("calculator.py") is False
    assert is_sensitive_file("pyproject.toml") is False
    assert is_sensitive_file("README.md") is False


def test_stack_trace_hints_extraction() -> None:
    stdout = """
============================= test session starts ==============================
FAILED tests/test_bug.py::test_divide_bug - assert 20 == 5
tests/test_bug.py:5: AssertionError
"""
    stderr = """
Traceback (most recent call last):
  File "/workspace/src/calculator.py", line 4, in divide
    return a * b
ZeroDivisionError: division by zero
"""
    hints = extract_stack_trace_hints(stdout, stderr)

    filenames = [h.file for h in hints]
    assert "src/calculator.py" in filenames
    assert "tests/test_bug.py" in filenames

    # Check line & symbol
    calc_hint = next(h for h in hints if h.file == "src/calculator.py")
    assert calc_hint.line == 4
    assert calc_hint.symbol == "divide"

    bug_hint = next(
        h
        for h in hints
        if h.file == "tests/test_bug.py" and h.symbol == "test_divide_bug"
    )
    assert bug_hint.symbol == "test_divide_bug"


def test_build_repository_tree() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "src").mkdir()
        (root / "src" / "main.py").write_text("print('hello')")
        (root / "tests").mkdir()
        (root / "tests" / "test_main.py").write_text("def test(): pass")
        (root / ".env").write_text("SECRET=123")  # Must be omitted
        (root / "__pycache__").mkdir()  # Ignored dir
        (root / "__pycache__" / "cached.pyc").write_text("bin")

        tree = build_repository_tree(root, max_entries=50)

        assert "main.py" in tree
        assert "test_main.py" in tree
        assert ".env" not in tree
        assert "__pycache__" not in tree


def test_build_investigation_context_bounds() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "src").mkdir()
        (root / "tests").mkdir()

        (root / "src" / "calc.py").write_text("def add(a, b): return a + b\n" * 50)
        (root / "tests" / "test_calc.py").write_text("def test_add(): assert True\n")
        (root / "secret.key").write_text("supersecret")  # Sensitive file

        settings = Settings(
            MAX_CONTEXT_FILES=5,
            MAX_CONTEXT_BYTES=5000,
            MAX_FILE_BYTES=200,
            MAX_TREE_ENTRIES=50,
            MAX_STDOUT_CONTEXT_BYTES=100,
            MAX_STDERR_CONTEXT_BYTES=100,
        )

        stdout = "x" * 200
        stderr = "y" * 200

        context = build_investigation_context(root, stdout, stderr, settings)

        assert len(context.stdout) <= 150
        assert "[... STDOUT TRUNCATED" in context.stdout
        assert len(context.stderr) <= 150
        assert "[... STDERR TRUNCATED" in context.stderr

        assert "tests/test_calc.py" in context.test_files
        assert "src/calc.py" in context.source_files
        assert "secret.key" not in context.source_files

        # Verify file content bounding
        assert "[... FILE CONTENT TRUNCATED ...]" in context.source_files["src/calc.py"]


def test_context_builder_nonexistent_directory() -> None:
    settings = Settings()
    with pytest.raises(LifecycleException) as exc_info:
        build_investigation_context(Path("/nonexistent/path/evida"), "", "", settings)
    assert exc_info.value.code == "AI_CONTEXT_BUILD_FAILED"
