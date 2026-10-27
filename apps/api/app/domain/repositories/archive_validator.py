"""Secure ZIP Archive Validator and Extractor

Enforces security boundaries on untrusted repository archives, preventing path
traversal, zip bombs, symlink escapes, and resource exhaustion.
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings
from app.domain.investigations.state_machine import LifecycleException


class ArchiveSecurityError(LifecycleException):
    """Raised when an archive violates security constraints."""

    def __init__(self, message: str, code: str = "INVALID_ARCHIVE", status_code: int = 400) -> None:
        super().__init__(message=message, code=code, status_code=status_code)


@dataclass
class ValidatedArchiveMetadata:
    filename: str
    size_bytes: int
    sha256_hash: str
    file_count: int
    total_uncompressed_bytes: int


def calculate_sha256(data: bytes) -> str:
    """Compute SHA-256 digest of binary content."""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


def validate_zip_archive(
    zip_bytes: bytes, filename: str, settings: Settings
) -> ValidatedArchiveMetadata:
    """Validate archive structure and security constraints prior to extraction.

    Raises:
        ArchiveSecurityError: If any security constraint or size limit is violated.
    """
    archive_size = len(zip_bytes)
    max_archive_bytes = settings.MAX_ARCHIVE_SIZE_MB * 1024 * 1024
    if archive_size > max_archive_bytes:
        raise ArchiveSecurityError(
            f"Archive size ({archive_size} bytes) exceeds limit of {settings.MAX_ARCHIVE_SIZE_MB}MB.",
            code="ARCHIVE_TOO_LARGE",
            status_code=413,
        )

    if archive_size == 0:
        raise ArchiveSecurityError("Archive is empty.", code="INVALID_ARCHIVE")

    sha256_hash = calculate_sha256(zip_bytes)

    try:
        archive_buffer = io.BytesIO(zip_bytes)
        if not zipfile.is_zipfile(archive_buffer):
            raise ArchiveSecurityError(
                "Uploaded file is not a valid ZIP archive.", code="INVALID_ARCHIVE"
            )

        archive_buffer.seek(0)
        with zipfile.ZipFile(archive_buffer, mode="r") as zf:
            infolist = zf.infolist()
            file_count = len(infolist)

            if file_count > settings.MAX_FILE_COUNT:
                raise ArchiveSecurityError(
                    f"Archive file count ({file_count}) exceeds limit of {settings.MAX_FILE_COUNT}.",
                    code="ARCHIVE_TOO_MANY_FILES",
                )

            total_uncompressed = 0
            max_single_file_bytes = settings.MAX_SINGLE_FILE_SIZE_MB * 1024 * 1024
            max_extracted_bytes = settings.MAX_EXTRACTED_SIZE_MB * 1024 * 1024

            for info in infolist:
                # 1. Reject absolute paths
                name = info.filename
                if os.path.isabs(name) or name.startswith("/") or name.startswith("\\"):
                    raise ArchiveSecurityError(
                        f"Archive contains illegal absolute path: '{name}'.",
                        code="INVALID_ARCHIVE",
                    )

                # 2. Reject path traversal
                parts = Path(name).parts
                if ".." in parts:
                    raise ArchiveSecurityError(
                        f"Archive contains path traversal sequence ('..'): '{name}'.",
                        code="INVALID_ARCHIVE",
                    )

                # 3. Check single file uncompressed size
                if info.file_size > max_single_file_bytes:
                    raise ArchiveSecurityError(
                        f"File '{name}' uncompressed size exceeds limit of {settings.MAX_SINGLE_FILE_SIZE_MB}MB.",
                        code="ARCHIVE_TOO_LARGE",
                        status_code=413,
                    )

                total_uncompressed += info.file_size
                if total_uncompressed > max_extracted_bytes:
                    raise ArchiveSecurityError(
                        f"Total extracted archive size exceeds limit of {settings.MAX_EXTRACTED_SIZE_MB}MB.",
                        code="ARCHIVE_TOO_LARGE",
                        status_code=413,
                    )

            return ValidatedArchiveMetadata(
                filename=filename,
                size_bytes=archive_size,
                sha256_hash=sha256_hash,
                file_count=file_count,
                total_uncompressed_bytes=total_uncompressed,
            )

    except zipfile.BadZipFile as exc:
        raise ArchiveSecurityError(
            f"Corrupted or invalid ZIP archive: {exc}", code="INVALID_ARCHIVE"
        ) from exc


def extract_archive_safely(zip_bytes: bytes, target_dir: Path, settings: Settings) -> Path:
    """Extract validated archive into target directory and return repository root path.

    Never uses blind extractall(). Verifies canonical destination for each item.
    """
    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    archive_buffer = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(archive_buffer, mode="r") as zf:
        for member in zf.infolist():
            # Canonical path verification
            member_path = (target_dir / member.filename).resolve()
            try:
                member_path.relative_to(target_dir)
            except ValueError as exc:
                raise ArchiveSecurityError(
                    f"Path escape attempt detected for member: {member.filename}",
                    code="INVALID_ARCHIVE",
                ) from exc

            # Skip directories or create them
            if member.is_dir():
                member_path.mkdir(parents=True, exist_ok=True)
                continue

            # Ensure parent directories exist
            member_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy stream
            with zf.open(member) as source, open(member_path, "wb") as dest:
                shutil.copyfileobj(source, dest)

    return detect_repository_root(target_dir)


def detect_repository_root(extraction_dir: Path) -> Path:
    """Detect actual repository root inside extracted directory.

    If the archive extracted to a single top-level directory (e.g., project/...),
    that directory is returned as the repository root. Otherwise, extraction_dir is returned.
    """
    entries = [p for p in extraction_dir.iterdir() if not p.name.startswith(".")]
    if len(entries) == 1 and entries[0].is_dir():
        # Check if the single directory contains files
        return entries[0]
    return extraction_dir
