"""Deterministic test fixtures generator for Phase 2 validation.

Creates:
- tests/fixtures/broken_python_repo.zip
- tests/fixtures/passing_python_repo.zip
- tests/fixtures/malicious_traversal.zip
"""

import io
import zipfile
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent


def create_broken_repo_zip() -> Path:
    target = FIXTURES_DIR / "broken_python_repo.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # App layout: root/src and root/tests
        zf.writestr(
            "broken_repo/src/__init__.py",
            "",
        )
        zf.writestr(
            "broken_repo/src/calculator.py",
            "def divide(a: int, b: int) -> int:\n    # Bug: multiplication instead of division\n    return a * b\n",
        )
        zf.writestr(
            "broken_repo/tests/__init__.py",
            "",
        )
        zf.writestr(
            "broken_repo/tests/test_bug.py",
            "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))\nfrom calculator import divide\n\ndef test_divide_bug():\n    assert divide(10, 2) == 5\n",
        )
        zf.writestr(
            "broken_repo/pyproject.toml",
            "[project]\nname = 'calculator-bug'\nversion = '0.1.0'\n",
        )
    target.write_bytes(buf.getvalue())
    return target


def create_passing_repo_zip() -> Path:
    target = FIXTURES_DIR / "passing_python_repo.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "passing_repo/src/__init__.py",
            "",
        )
        zf.writestr(
            "passing_repo/src/calculator.py",
            "def divide(a: int, b: int) -> int:\n    return a // b\n",
        )
        zf.writestr(
            "passing_repo/tests/__init__.py",
            "",
        )
        zf.writestr(
            "passing_repo/tests/test_bug.py",
            "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))\nfrom calculator import divide\n\ndef test_divide_bug():\n    assert divide(10, 2) == 5\n",
        )
        zf.writestr(
            "passing_repo/pyproject.toml",
            "[project]\nname = 'calculator-passing'\nversion = '0.1.0'\n",
        )
    target.write_bytes(buf.getvalue())
    return target


def create_malicious_traversal_zip() -> Path:
    target = FIXTURES_DIR / "malicious_traversal.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("valid_file.txt", "harmless content")
        zf.writestr("../evil_file.py", "import os; os.system('echo pwned')")
    target.write_bytes(buf.getvalue())
    return target


if __name__ == "__main__":
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    p1 = create_broken_repo_zip()
    p2 = create_passing_repo_zip()
    p3 = create_malicious_traversal_zip()
    print(f"Generated fixtures:\n - {p1}\n - {p2}\n - {p3}")
