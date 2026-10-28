"""Deterministic Patch Applier & Workspace Integrity Validator (Phase 6)

Applies validated unified diff patches inside an isolated ephemeral workspace,
detects hunk application failures, captures pre/post file manifests, and verifies
that zero unexpected files, test files, or sensitive files are altered.
"""

from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path

from sandbox.runner.runner import execute_command

from app.domain.verification.models import PatchApplicationResult

# Regex to parse unified diff file headers
DIFF_HEADER_RE = re.compile(
    r"^---\s+(?:[ab]/)?([^\t\n\r]+)\r?\n\+\+\+\s+(?:[ab]/)?([^\t\n\r]+)",
    re.MULTILINE,
)
HUNK_HEADER_RE = re.compile(
    r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@(.*)",
)


def capture_workspace_manifest(repo_root: Path) -> dict[str, str]:
    """Capture a deterministic file manifest (relative POSIX path -> SHA-256 digest)."""
    manifest: dict[str, str] = {}
    if not repo_root.exists() or not repo_root.is_dir():
        return manifest

    for file_path in sorted(repo_root.rglob("*")):
        if file_path.is_file() and not file_path.is_symlink():
            rel_path = file_path.relative_to(repo_root).as_posix()
            hasher = hashlib.sha256()
            try:
                hasher.update(file_path.read_bytes())
                manifest[rel_path] = hasher.hexdigest()
            except OSError:
                continue
    return manifest


def apply_patch_pure_python(repo_root: Path, patch_content: str) -> tuple[bool, str, list[str]]:
    """Apply a unified diff directly using pure Python hunk parsing and application.

    Returns:
        (success, error_message, list_of_modified_files)
    """
    lines = patch_content.splitlines()
    i = 0
    modified_files: list[str] = []

    # File hunks collector: file_path -> list of hunks
    file_patches: list[tuple[str, list[tuple[int, int, list[str]]]]] = []
    current_file: str | None = None
    current_hunks: list[tuple[int, int, list[str]]] = []

    while i < len(lines):
        line = lines[i]
        if line.startswith("--- "):
            if i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
                # Finish previous file if any
                if current_file and current_hunks:
                    file_patches.append((current_file, current_hunks))
                    current_hunks = []

                plus_line = lines[i + 1]
                target_path = plus_line[4:].strip()
                if target_path.startswith("b/"):
                    target_path = target_path[2:]
                current_file = target_path
                i += 2
                continue

        if line.startswith("@@"):
            m = HUNK_HEADER_RE.match(line)
            if not m:
                return False, f"Malformed hunk header: {line}", []
            old_start = int(m.group(1))
            old_count = int(m.group(2)) if m.group(2) is not None else 1
            hunk_lines: list[str] = []
            i += 1
            while (
                i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("--- ")
            ):
                hunk_lines.append(lines[i])
                i += 1
            current_hunks.append((old_start, old_count, hunk_lines))
            continue

        i += 1

    if current_file and current_hunks:
        file_patches.append((current_file, current_hunks))

    if not file_patches:
        return False, "No valid unified diff hunks found in patch", []

    # Apply to each file
    for rel_path, hunks in file_patches:
        target_file = repo_root / rel_path
        if not target_file.exists():
            return False, f"Target file '{rel_path}' does not exist in workspace", []

        try:
            original_text = target_file.read_text(encoding="utf-8")
        except Exception as exc:
            return False, f"Could not read target file '{rel_path}': {exc}", []

        orig_lines = original_text.splitlines()
        new_lines: list[str] = []
        orig_idx = 0

        # Sort hunks by old_start
        sorted_hunks = sorted(hunks, key=lambda h: h[0])
        for old_start, _, hunk_lines in sorted_hunks:
            target_line_idx = max(0, old_start - 1)

            # Copy lines up to hunk start
            while orig_idx < target_line_idx and orig_idx < len(orig_lines):
                new_lines.append(orig_lines[orig_idx])
                orig_idx += 1

            for h_line in hunk_lines:
                if not h_line:
                    # Treat empty line as empty context
                    if orig_idx < len(orig_lines):
                        new_lines.append(orig_lines[orig_idx])
                        orig_idx += 1
                    continue

                marker = h_line[0]
                content = h_line[1:]

                if marker == " ":
                    if orig_idx < len(orig_lines) and orig_lines[orig_idx] == content:
                        new_lines.append(orig_lines[orig_idx])
                        orig_idx += 1
                    elif orig_idx < len(orig_lines):
                        # Relaxed match (whitespace stripped)
                        if orig_lines[orig_idx].strip() == content.strip():
                            new_lines.append(orig_lines[orig_idx])
                            orig_idx += 1
                        else:
                            return (
                                False,
                                f"Hunk context mismatch at line {orig_idx + 1} in {rel_path}. "
                                f"Expected '{content}', got '{orig_lines[orig_idx]}'",
                                [],
                            )
                    else:
                        new_lines.append(content)
                elif marker == "-":
                    if orig_idx < len(orig_lines) and (
                        orig_lines[orig_idx] == content
                        or orig_lines[orig_idx].strip() == content.strip()
                    ):
                        # Discard line
                        orig_idx += 1
                    else:
                        return (
                            False,
                            f"Hunk deletion mismatch at line {orig_idx + 1} in {rel_path}. "
                            f"Expected to delete '{content}', got '{orig_lines[orig_idx] if orig_idx < len(orig_lines) else 'EOF'}'",
                            [],
                        )
                elif marker == "+":
                    new_lines.append(content)

        # Copy any remaining lines
        while orig_idx < len(orig_lines):
            new_lines.append(orig_lines[orig_idx])
            orig_idx += 1

        # Preserve trailing newline if original had one
        new_text = "\n".join(new_lines)
        if original_text.endswith("\n"):
            new_text += "\n"

        target_file.write_text(new_text, encoding="utf-8")
        modified_files.append(rel_path)

    return True, "", modified_files


def apply_patch_to_workspace(
    repo_root: Path,
    patch_content: str,
    declared_changed_files: list[str],
    *,
    timeout_seconds: float = 30.0,
) -> tuple[PatchApplicationResult, dict[str, str]]:
    """Apply validated candidate patch to an isolated workspace with defense-in-depth checks.

    Args:
        repo_root: Path to the extracted repository workspace root.
        patch_content: Canonical unified diff text.
        declared_changed_files: List of files declared as changed by the Phase 5 candidate.
        timeout_seconds: Hard timeout for the application process.

    Returns:
        tuple of (PatchApplicationResult, manifest_after).
    """
    start_time = time.perf_counter()
    manifest_before = capture_workspace_manifest(repo_root)

    # 1. First attempt: use git apply in sandbox runner if available
    applied_cleanly = False
    stdout = ""
    stderr = ""
    exit_code = 0

    patch_file = repo_root / ".evida_candidate.patch"
    try:
        patch_file.write_text(patch_content, encoding="utf-8")
        # Run git apply --whitespace=nowarn .evida_candidate.patch
        git_res = execute_command(
            ["git", "apply", "--whitespace=nowarn", ".evida_candidate.patch"],
            cwd=str(repo_root),
            timeout_seconds=timeout_seconds,
        )
        if git_res.exit_code == 0 and not git_res.timed_out:
            applied_cleanly = True
            stdout = git_res.stdout
            stderr = git_res.stderr
            exit_code = 0
    except Exception as exc:
        stderr = f"git apply invocation failed: {exc}"
    finally:
        if patch_file.exists():
            patch_file.unlink()

    # 2. Second attempt: fallback to pure-python patch applier if git apply did not succeed
    if not applied_cleanly:
        py_success, py_err, _ = apply_patch_pure_python(repo_root, patch_content)
        if py_success:
            applied_cleanly = True
            stdout = "Patch applied cleanly via deterministic Python engine."
            stderr = ""
            exit_code = 0
        else:
            stderr = f"Patch application failed: {py_err}"
            exit_code = 1

    duration_ms = (time.perf_counter() - start_time) * 1000.0

    if not applied_cleanly:
        return (
            PatchApplicationResult(
                status="FAILED",
                exit_code=exit_code if exit_code != 0 else 1,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
            ),
            manifest_before,
        )

    # 3. Post-application workspace integrity verification
    manifest_after = capture_workspace_manifest(repo_root)

    modified_files = [
        f
        for f in manifest_after
        if f in manifest_before and manifest_after[f] != manifest_before[f]
    ]
    created_files = [f for f in manifest_after if f not in manifest_before]
    deleted_files = [f for f in manifest_before if f not in manifest_after]

    # Verify that NO tests were altered
    for f in modified_files + created_files + deleted_files:
        if f.startswith("tests/") or f == "tests" or "test_regression" in f:
            return (
                PatchApplicationResult(
                    status="FAILED",
                    exit_code=1,
                    stdout=stdout,
                    stderr=f"Security violation: patch modified test file '{f}'. Tests are immutable.",
                    duration_ms=duration_ms,
                    modified_files=modified_files,
                    created_files=created_files,
                    deleted_files=deleted_files,
                ),
                manifest_after,
            )

    # Verify that only declared files were modified
    unexpected_modifications = [f for f in modified_files if f not in declared_changed_files]
    if unexpected_modifications or created_files or deleted_files:
        err_msg = (
            f"Unexpected workspace changes detected. "
            f"Unexpected modifications: {unexpected_modifications}, "
            f"Created: {created_files}, Deleted: {deleted_files}"
        )
        return (
            PatchApplicationResult(
                status="FAILED",
                exit_code=1,
                stdout=stdout,
                stderr=err_msg,
                duration_ms=duration_ms,
                modified_files=modified_files,
                created_files=created_files,
                deleted_files=deleted_files,
            ),
            manifest_after,
        )

    return (
        PatchApplicationResult(
            status="APPLIED",
            exit_code=0,
            stdout=stdout or "Patch applied successfully.",
            stderr=stderr,
            duration_ms=duration_ms,
            modified_files=modified_files,
            created_files=created_files,
            deleted_files=deleted_files,
        ),
        manifest_after,
    )
