"""Deterministic Unified Diff and Patch Security Validator (Phase 5)

Performs deterministic structural, path safety, sensitive-file exclusion,
test-immutability, and security inspection on AI-generated candidate patches.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Final

from app.core.config import Settings
from app.domain.patches.models import (
    PatchProposal,
    PatchValidationClassification,
    PatchValidationResult,
)

# Sensitive patterns that must NEVER be modified by patches
SENSITIVE_FILE_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),
    re.compile(r"^.*\.pem$", re.IGNORECASE),
    re.compile(r"^.*\.key$", re.IGNORECASE),
    re.compile(r"^.*\.p12$", re.IGNORECASE),
    re.compile(r"^.*\.pfx$", re.IGNORECASE),
    re.compile(r"^credentials\.json$", re.IGNORECASE),
    re.compile(r"^service[-_]account\.json$", re.IGNORECASE),
    re.compile(r"^id_rsa.*$", re.IGNORECASE),
    re.compile(r"^id_ed25519.*$", re.IGNORECASE),
    re.compile(r"^Dockerfile.*$", re.IGNORECASE),
    re.compile(r"^docker-compose.*\.ya?ml$", re.IGNORECASE),
    re.compile(r"^\.github/.*$", re.IGNORECASE),
    re.compile(r"^sandbox/.*$", re.IGNORECASE),
]

# Dangerous call patterns forbidden in added lines of candidate patches
DANGEROUS_DIFF_PATTERNS: Final[list[tuple[re.Pattern[str], str]]] = [
    (
        re.compile(r"\bsubprocess\.(Popen|run|call|check_call|check_output)\b"),
        "subprocess execution",
    ),
    (
        re.compile(r"\bos\.(system|popen|kill|remove|unlink|rmdir)\b"),
        "os system command / deletion",
    ),
    (re.compile(r"\bshutil\.(rmtree|move)\b"), "shutil deletion"),
    (re.compile(r"\b(eval|exec)\s*\("), "dynamic eval/exec"),
    (re.compile(r"\b__import__\s*\("), "dynamic __import__"),
    (re.compile(r"\bsocket\.(socket|create_connection)\b"), "raw socket networking"),
    (
        re.compile(r"\b(requests|httpx|urllib|aiohttp)\.(get|post|put|delete|request)\b"),
        "network HTTP request",
    ),
    (re.compile(r"\b(pip|apt|apt-get|apk|yum)\s+install\b"), "package installation attempt"),
    (re.compile(r"GIT binary patch", re.IGNORECASE), "binary patch content"),
]


def clean_diff_path(raw_path: str) -> str:
    """Normalize diff header paths (e.g. 'a/src/calculator.py' -> 'src/calculator.py')."""
    clean = raw_path.strip()
    if clean.startswith("a/") or clean.startswith("b/"):
        clean = clean[2:]
    return clean


def parse_unified_diff_files_and_hunks(diff_content: str) -> tuple[list[str], int, list[str]]:
    """Parse diff content to extract actual modified files, hunk count, and added lines."""
    parsed_files: list[str] = []
    hunk_count = 0
    added_lines: list[str] = []

    lines = diff_content.splitlines()
    for line in lines:
        if line.startswith("+++ "):
            raw_target = line[4:].strip().split("\t")[0]
            if raw_target != "/dev/null":
                norm_target = clean_diff_path(raw_target)
                if norm_target and norm_target not in parsed_files:
                    parsed_files.append(norm_target)
        elif line.startswith("@@ ") and " @@" in line:
            hunk_count += 1
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])

    return parsed_files, hunk_count, added_lines


def validate_patch_proposal(
    proposal: PatchProposal,
    settings: Settings,
    *,
    existing_repo_files: set[str] | None = None,
    allowed_affected_files: set[str] | None = None,
) -> PatchValidationResult:
    """Deterministically validates format, paths, test immutability, scope, and security of patch proposal."""
    # 1. Format Check
    if proposal.patch_format != "unified_diff":
        return PatchValidationResult(
            is_valid=False,
            classification=PatchValidationClassification.INVALID_FORMAT,
            errors=[
                f"Unsupported patch format '{proposal.patch_format}'; expected 'unified_diff'."
            ],
        )

    # 2. Size Check
    patch_bytes = len(proposal.patch_content.encode("utf-8"))
    if patch_bytes > settings.MAX_GENERATED_PATCH_BYTES:
        return PatchValidationResult(
            is_valid=False,
            classification=PatchValidationClassification.PATCH_TOO_LARGE,
            errors=[
                f"Patch size {patch_bytes} bytes exceeds limit {settings.MAX_GENERATED_PATCH_BYTES} bytes."
            ],
        )

    if not proposal.patch_content.strip():
        return PatchValidationResult(
            is_valid=False,
            classification=PatchValidationClassification.MALFORMED_DIFF,
            errors=["Patch content is empty."],
        )

    # 3. Parse Unified Diff Header & Hunks
    parsed_files, hunk_count, added_lines = parse_unified_diff_files_and_hunks(
        proposal.patch_content
    )

    if not parsed_files or hunk_count == 0:
        return PatchValidationResult(
            is_valid=False,
            classification=PatchValidationClassification.MALFORMED_DIFF,
            errors=[
                "Failed to parse valid unified diff headers (--- / +++) and hunks (@@ -... @@)."
            ],
        )

    if hunk_count > settings.MAX_PATCH_HUNKS:
        return PatchValidationResult(
            is_valid=False,
            classification=PatchValidationClassification.PATCH_TOO_LARGE,
            errors=[
                f"Patch contains {hunk_count} hunks, exceeding limit of {settings.MAX_PATCH_HUNKS}."
            ],
            parsed_files=parsed_files,
            hunk_count=hunk_count,
        )

    if len(parsed_files) > settings.MAX_PATCH_FILES:
        return PatchValidationResult(
            is_valid=False,
            classification=PatchValidationClassification.PATCH_TOO_LARGE,
            errors=[
                f"Patch targets {len(parsed_files)} files, exceeding limit of {settings.MAX_PATCH_FILES}."
            ],
            parsed_files=parsed_files,
            hunk_count=hunk_count,
        )

    # 4. Compare Declared changed_files vs Parsed Files
    declared_set = set(proposal.changed_files)
    parsed_set = set(parsed_files)
    if declared_set != parsed_set:
        return PatchValidationResult(
            is_valid=False,
            classification=PatchValidationClassification.MALFORMED_DIFF,
            errors=[
                f"Declared changed_files {sorted(declared_set)} does not match diff parsed files {sorted(parsed_set)}."
            ],
            parsed_files=parsed_files,
            hunk_count=hunk_count,
        )

    # 5. Path Safety Validation
    for target_path in parsed_files:
        try:
            posix_path = PurePosixPath(target_path)
        except Exception:
            return PatchValidationResult(
                is_valid=False,
                classification=PatchValidationClassification.PATH_VIOLATION,
                errors=[f"Invalid path format: '{target_path}'."],
                parsed_files=parsed_files,
            )

        if posix_path.is_absolute() or target_path.startswith("/") or target_path.startswith("\\"):
            return PatchValidationResult(
                is_valid=False,
                classification=PatchValidationClassification.PATH_VIOLATION,
                errors=[f"Absolute paths not permitted in candidate patch: '{target_path}'."],
                parsed_files=parsed_files,
            )

        if ":" in target_path or "\\" in target_path:
            return PatchValidationResult(
                is_valid=False,
                classification=PatchValidationClassification.PATH_VIOLATION,
                errors=[f"Invalid path characters in: '{target_path}'."],
                parsed_files=parsed_files,
            )

        if ".." in posix_path.parts:
            return PatchValidationResult(
                is_valid=False,
                classification=PatchValidationClassification.PATH_VIOLATION,
                errors=[f"Path traversal ('..') detected in: '{target_path}'."],
                parsed_files=parsed_files,
            )

    # 6. Sensitive File Exclusion
    for target_path in parsed_files:
        filename = PurePosixPath(target_path).name
        for pattern in SENSITIVE_FILE_PATTERNS:
            if pattern.search(target_path) or pattern.search(filename):
                return PatchValidationResult(
                    is_valid=False,
                    classification=PatchValidationClassification.SENSITIVE_FILE_MODIFICATION,
                    errors=[
                        f"Modification of sensitive or security-restricted file '{target_path}' is forbidden."
                    ],
                    parsed_files=parsed_files,
                )

    # 7. Test Immutability Policy (Section 17)
    for target_path in parsed_files:
        posix_path = PurePosixPath(target_path)
        filename = posix_path.name
        is_test_dir = "tests" in posix_path.parts or "test" in posix_path.parts
        is_test_file = (
            filename.startswith("test_")
            or filename.endswith("_test.py")
            or filename == "conftest.py"
        )

        if is_test_dir or is_test_file:
            return PatchValidationResult(
                is_valid=False,
                classification=PatchValidationClassification.TEST_MODIFICATION,
                errors=[
                    f"Modifying test file '{target_path}' is strictly forbidden in Phase 5 patch synthesis."
                ],
                parsed_files=parsed_files,
            )

    # 8. Scope & Existence Validation
    if existing_repo_files is not None:
        for target_path in parsed_files:
            if target_path not in existing_repo_files:
                return PatchValidationResult(
                    is_valid=False,
                    classification=PatchValidationClassification.FILE_NOT_FOUND,
                    errors=[
                        f"Target file '{target_path}' does not exist in the original repository."
                    ],
                    parsed_files=parsed_files,
                )

    if allowed_affected_files is not None and allowed_affected_files:
        # Check that target files fall within affected / source files scope
        for target_path in parsed_files:
            if target_path not in allowed_affected_files:
                return PatchValidationResult(
                    is_valid=False,
                    classification=PatchValidationClassification.OUT_OF_SCOPE_CHANGE,
                    errors=[
                        f"Target file '{target_path}' is outside the confirmed affected scope {sorted(allowed_affected_files)}."
                    ],
                    parsed_files=parsed_files,
                )

    # 9. Security Inspection on Added Lines
    for line in added_lines:
        for danger_pattern, description in DANGEROUS_DIFF_PATTERNS:
            if danger_pattern.search(line):
                return PatchValidationResult(
                    is_valid=False,
                    classification=PatchValidationClassification.SECURITY_VIOLATION,
                    errors=[
                        f"Dangerous construct detected in patch: {description} (line: '{line.strip()}')."
                    ],
                    parsed_files=parsed_files,
                )

    # Passed all deterministic validation gates!
    return PatchValidationResult(
        is_valid=True,
        classification=PatchValidationClassification.VALID,
        errors=[],
        parsed_files=parsed_files,
        hunk_count=hunk_count,
    )
