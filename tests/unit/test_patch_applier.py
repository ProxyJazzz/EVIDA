"""Unit tests for Phase 6 Patch Applier & Workspace Integrity Validator."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.domain.verification.patch_applier import (
    apply_patch_pure_python,
    apply_patch_to_workspace,
    capture_workspace_manifest,
)


def test_capture_workspace_manifest():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        (root / "src" / "a.py").write_text("print('hello')", encoding="utf-8")
        manifest = capture_workspace_manifest(root)
        assert "src/a.py" in manifest
        assert len(manifest["src/a.py"]) == 64  # SHA-256


def test_apply_patch_pure_python_success():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        calc = root / "src" / "calculator.py"
        calc.write_text("def divide(a, b):\n    return a * b\n", encoding="utf-8")

        patch = (
            "--- a/src/calculator.py\n"
            "+++ b/src/calculator.py\n"
            "@@ -1,2 +1,2 @@\n"
            " def divide(a, b):\n"
            "-    return a * b\n"
            "+    return a / b\n"
        )

        ok, err, modified = apply_patch_pure_python(root, patch)
        assert ok is True
        assert err == ""
        assert modified == ["src/calculator.py"]
        assert (
            calc.read_text(encoding="utf-8") == "def divide(a, b):\n    return a / b\n"
        )


def test_apply_patch_pure_python_missing_target():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        patch = (
            "--- a/src/nonexistent.py\n"
            "+++ b/src/nonexistent.py\n"
            "@@ -1,1 +1,1 @@\n"
            "-foo\n"
            "+bar\n"
        )
        ok, err, _modified = apply_patch_pure_python(root, patch)
        assert ok is False
        assert "does not exist" in err


def test_apply_patch_pure_python_context_mismatch():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        calc = root / "src" / "calculator.py"
        calc.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

        patch = (
            "--- a/src/calculator.py\n"
            "+++ b/src/calculator.py\n"
            "@@ -1,2 +1,2 @@\n"
            " def divide(a, b):\n"
            "-    return a * b\n"
            "+    return a / b\n"
        )
        ok, err, _ = apply_patch_pure_python(root, patch)
        assert ok is False
        assert "mismatch" in err


def test_apply_patch_to_workspace_clean():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        calc = root / "src" / "calculator.py"
        calc.write_text("def divide(a, b):\n    return a * b\n", encoding="utf-8")

        patch = (
            "--- a/src/calculator.py\n"
            "+++ b/src/calculator.py\n"
            "@@ -1,2 +1,2 @@\n"
            " def divide(a, b):\n"
            "-    return a * b\n"
            "+    return a / b\n"
        )

        res, _manifest = apply_patch_to_workspace(
            root, patch, declared_changed_files=["src/calculator.py"]
        )
        assert res.status == "APPLIED"
        assert res.exit_code == 0
        assert res.modified_files == ["src/calculator.py"]
        assert (
            calc.read_text(encoding="utf-8") == "def divide(a, b):\n    return a / b\n"
        )


def test_apply_patch_to_workspace_rejects_test_modification():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tests").mkdir()
        test_file = root / "tests" / "test_dummy.py"
        test_file.write_text("assert True\n", encoding="utf-8")

        patch = (
            "--- a/tests/test_dummy.py\n"
            "+++ b/tests/test_dummy.py\n"
            "@@ -1,1 +1,1 @@\n"
            "-assert True\n"
            "+assert False\n"
        )
        res, _ = apply_patch_to_workspace(
            root, patch, declared_changed_files=["tests/test_dummy.py"]
        )
        assert res.status == "FAILED"
        assert "test file" in res.stderr.lower()


def test_apply_patch_to_workspace_rejects_unexpected_file_modification():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        (root / "src" / "other.py").write_text("val = 1\n", encoding="utf-8")

        patch = (
            "--- a/src/other.py\n"
            "+++ b/src/other.py\n"
            "@@ -1,1 +1,1 @@\n"
            "-val = 1\n"
            "+val = 2\n"
        )
        # Declared files only specifies src/calculator.py
        res, _ = apply_patch_to_workspace(
            root, patch, declared_changed_files=["src/calculator.py"]
        )
        assert res.status == "FAILED"
        assert "unexpected" in res.stderr.lower()
