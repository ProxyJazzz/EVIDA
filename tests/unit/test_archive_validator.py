"""Unit Tests for Secure ZIP Archive Validation (Phase 2)."""

import io
import tempfile
import zipfile
from pathlib import Path

import pytest
from app.core.config import Settings
from app.domain.investigations.state_machine import LifecycleException
from app.domain.repositories.archive_validator import (
    calculate_sha256,
    detect_repository_root,
    extract_archive_safely,
    validate_zip_archive,
)


@pytest.fixture
def default_settings() -> Settings:
    return Settings(
        MAX_ARCHIVE_SIZE_MB=5,
        MAX_EXTRACTED_SIZE_MB=10,
        MAX_FILE_COUNT=20,
        MAX_SINGLE_FILE_SIZE_MB=2,
    )


def test_calculate_sha256() -> None:
    data = b"EVIDA: AI proposes. Evidence decides."
    digest = calculate_sha256(data)
    assert isinstance(digest, str)
    assert len(digest) == 64
    # Deterministic check
    assert calculate_sha256(data) == digest


def test_validate_zip_archive_success(default_settings: Settings) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("src/main.py", "print('hello world')")
        zf.writestr("tests/test_main.py", "def test(): pass")

    content = buf.getvalue()
    meta = validate_zip_archive(content, "repo.zip", default_settings)

    assert meta.filename == "repo.zip"
    assert meta.file_count == 2
    assert meta.size_bytes == len(content)
    assert meta.sha256_hash == calculate_sha256(content)


def test_reject_non_zip_content(default_settings: Settings) -> None:
    with pytest.raises(LifecycleException) as exc_info:
        validate_zip_archive(b"this is not a zip file", "repo.zip", default_settings)
    assert exc_info.value.code == "INVALID_ARCHIVE"


def test_reject_archive_exceeding_max_size() -> None:
    strict_settings = Settings(MAX_ARCHIVE_SIZE_MB=1)  # 1 MB max
    oversized = b"0" * (1024 * 1024 + 50)
    with pytest.raises(LifecycleException) as exc_info:
        validate_zip_archive(oversized, "huge.zip", strict_settings)
    assert exc_info.value.code == "ARCHIVE_TOO_LARGE"


def test_reject_path_traversal(default_settings: Settings) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("safe.txt", "safe")
        zf.writestr("../etc/passwd", "root:x:0:0")

    content = buf.getvalue()
    with pytest.raises(LifecycleException) as exc_info:
        validate_zip_archive(content, "traversal.zip", default_settings)
    assert exc_info.value.code == "INVALID_ARCHIVE"
    assert "traversal" in exc_info.value.message.lower()


def test_reject_absolute_path_in_zip(default_settings: Settings) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("/root/secret.txt", "secret")

    content = buf.getvalue()
    with pytest.raises(LifecycleException) as exc_info:
        validate_zip_archive(content, "absolute.zip", default_settings)
    assert exc_info.value.code == "INVALID_ARCHIVE"
    assert "absolute" in exc_info.value.message.lower()


def test_reject_too_many_files(default_settings: Settings) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(25):  # default_settings has limit of 20
            zf.writestr(f"file_{i}.txt", f"data {i}")

    content = buf.getvalue()
    with pytest.raises(LifecycleException) as exc_info:
        validate_zip_archive(content, "many.zip", default_settings)
    assert exc_info.value.code == "ARCHIVE_TOO_MANY_FILES"


def test_reject_single_file_too_large(default_settings: Settings) -> None:
    strict_settings = Settings(MAX_SINGLE_FILE_SIZE_MB=1)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        # Create uncompressed large file
        zf.writestr("large.txt", b"x" * (1024 * 1024 + 100))

    content = buf.getvalue()
    with pytest.raises(LifecycleException) as exc_info:
        validate_zip_archive(content, "large_file.zip", strict_settings)
    assert exc_info.value.code == "ARCHIVE_TOO_LARGE"


def test_detect_repository_root_nested() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        nested = tmp_path / "my_project"
        nested.mkdir()
        (nested / "src").mkdir()
        (nested / "src" / "main.py").write_text("print('test')")

        detected = detect_repository_root(tmp_path)
        assert detected == nested


def test_detect_repository_root_flat() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")

        detected = detect_repository_root(tmp_path)
        assert detected == tmp_path


def test_extract_archive_safely(default_settings: Settings) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("my_app/src/app.py", "def run(): return 42\n")
        zf.writestr("my_app/tests/test_app.py", "def test(): assert True\n")

    content = buf.getvalue()
    with tempfile.TemporaryDirectory() as tmp_dir:
        dest = Path(tmp_dir)
        root = extract_archive_safely(content, dest, default_settings)

        assert root.is_dir()
        assert (root / "src" / "app.py").exists()
        assert (root / "src" / "app.py").read_text() == "def run(): return 42\n"
