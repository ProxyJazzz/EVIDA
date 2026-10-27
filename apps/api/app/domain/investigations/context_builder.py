"""Repository Context Builder for AI Investigation (Phase 3).

Extracts bounded, prioritized, and sanitized context from an ingested repository
and reproduction evidence to feed the AI causal hypothesis engine.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import Settings
from app.domain.investigations.state_machine import LifecycleException

# Sensitive filenames and patterns that must NEVER be read or sent to AI
SENSITIVE_PATTERNS = {
    ".env*",
    "*.pem",
    "*.key",
    "*.pfx",
    "*.pkcs12",
    "credentials.json",
    "service-account*.json",
    "id_rsa*",
    "id_ed25519*",
    "*secret*",
    "*token*",
    "*password*",
}

# Directories that must be completely ignored
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".evida_storage",
    ".idea",
    ".vscode",
}

# Priority extensions
ALLOWED_EXTENSIONS = {
    ".py",
    ".pyi",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ini",
    ".cfg",
    ".md",
    ".txt",
}


@dataclass
class StackTraceHint:
    file: str
    line: int | None = None
    symbol: str | None = None


@dataclass
class RepositoryContext:
    tree: str
    source_files: dict[str, str] = field(default_factory=dict)
    test_files: dict[str, str] = field(default_factory=dict)
    traceback_hints: list[StackTraceHint] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    total_bytes: int = 0


def is_sensitive_file(filename: str) -> bool:
    """Check if a filename or path matches known sensitive file patterns."""
    basename = Path(filename).name.lower()
    for pattern in SENSITIVE_PATTERNS:
        if fnmatch.fnmatch(basename, pattern):
            return True
    return False


def is_binary_file(file_path: Path) -> bool:
    """Detect if a file contains binary content."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except Exception:
        return True


def extract_stack_trace_hints(stdout: str, stderr: str) -> list[StackTraceHint]:
    """Deterministically parse Python tracebacks and pytest failure summaries."""
    hints: list[StackTraceHint] = []
    seen: set[tuple[str, int | None, str | None]] = set()

    combined_text = f"{stdout}\n{stderr}"

    # 1. Standard Python traceback pattern: File "...", line X, in Y
    py_trace_regex = re.compile(
        r'File\s+"(?:.+?[/\\])?([^"]+)",\s+line\s+(\d+)(?:,\s+in\s+([a-zA-Z0-9_]+))?'
    )
    for match in py_trace_regex.finditer(combined_text):
        fname = match.group(1).replace("\\", "/")
        line = int(match.group(2))
        symbol = match.group(3)
        key1: tuple[str, int | None, str | None] = (fname, line, symbol)
        if key1 not in seen:
            seen.add(key1)
            hints.append(StackTraceHint(file=fname, line=line, symbol=symbol))

    # 2. Pytest test failure pattern: FAILED tests/test_bug.py::test_divide_bug
    pytest_fail_regex = re.compile(r"FAILED\s+([^\s:]+)(?:::([a-zA-Z0-9_]+))?")
    for match in pytest_fail_regex.finditer(combined_text):
        fname = match.group(1).replace("\\", "/")
        symbol = match.group(2)
        key2: tuple[str, int | None, str | None] = (fname, None, symbol)
        if key2 not in seen:
            seen.add(key2)
            hints.append(StackTraceHint(file=fname, line=None, symbol=symbol))

    # 3. Pytest assertion line location: tests/test_bug.py:5: AssertionError
    pytest_assert_regex = re.compile(r"^([^\s:]+\.py):(\d+):\s+[A-Za-z0-9_]*Error", re.MULTILINE)
    for match in pytest_assert_regex.finditer(combined_text):
        fname = match.group(1).replace("\\", "/")
        line = int(match.group(2))
        key3: tuple[str, int | None, str | None] = (fname, line, None)
        if key3 not in seen:
            seen.add(key3)
            hints.append(StackTraceHint(file=fname, line=line, symbol=None))

    return hints


def build_repository_tree(repo_root: Path, max_entries: int = 500) -> str:
    """Generate a bounded directory tree string for the repository."""
    lines: list[str] = []
    count = 0

    try:
        # Traverse topdown to skip ignored directories efficiently
        for root, dirs, files in repo_root.walk(top_down=True):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            dirs.sort()
            files.sort()

            rel_root = root.relative_to(repo_root)
            depth = len(rel_root.parts)
            indent = "  " * depth

            if depth > 0:
                lines.append(f"{indent[:-2]}📁 {rel_root.name}/")
                count += 1
                if count >= max_entries:
                    lines.append(f"{indent}[Tree truncated: reached {max_entries} entries limit]")
                    break

            for f in files:
                if is_sensitive_file(f):
                    continue
                lines.append(f"{indent}📄 {f}")
                count += 1
                if count >= max_entries:
                    lines.append(f"{indent}[Tree truncated: reached {max_entries} entries limit]")
                    break

            if count >= max_entries:
                break
    except Exception as exc:
        lines.append(f"[Error generating directory tree: {exc}]")

    return "\n".join(lines)


def build_investigation_context(
    repo_root: Path,
    stdout: str,
    stderr: str,
    settings: Settings,
) -> RepositoryContext:
    """Construct prioritized, bounded context for AI hypothesis generation.

    Enforces limits on:
    - Number of files
    - Bytes per file
    - Total context size
    - Tree entries
    - Stdout/stderr lengths
    """
    if not repo_root.exists() or not repo_root.is_dir():
        raise LifecycleException(
            f"Repository root directory '{repo_root}' does not exist.",
            code="AI_CONTEXT_BUILD_FAILED",
            status_code=500,
        )

    # 1. Bounded execution streams
    bounded_stdout = stdout[: settings.MAX_STDOUT_CONTEXT_BYTES]
    if len(stdout) > settings.MAX_STDOUT_CONTEXT_BYTES:
        bounded_stdout += "\n[... STDOUT TRUNCATED FOR CONTEXT ...]"

    bounded_stderr = stderr[: settings.MAX_STDERR_CONTEXT_BYTES]
    if len(stderr) > settings.MAX_STDERR_CONTEXT_BYTES:
        bounded_stderr += "\n[... STDERR TRUNCATED FOR CONTEXT ...]"

    # 2. Extract stack trace hints
    hints = extract_stack_trace_hints(stdout, stderr)

    # 3. Generate directory tree
    tree = build_repository_tree(repo_root, max_entries=settings.MAX_TREE_ENTRIES)

    # 4. Discover candidate files and score/prioritize them
    all_files: list[Path] = []
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue

        # Skip ignored dirs
        rel_parts = p.relative_to(repo_root).parts
        if any(part in IGNORED_DIRS or part.startswith(".") for part in rel_parts[:-1]):
            continue

        # Skip sensitive files
        if is_sensitive_file(p.name):
            continue

        # Skip binaries and unapproved extensions
        if p.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        if is_binary_file(p):
            continue

        all_files.append(p)

    hint_files = {h.file.lower() for h in hints}

    def score_file(path: Path) -> int:
        """Assign priority score (lower number = higher priority)."""
        rel = str(path.relative_to(repo_root)).replace("\\", "/")
        rel_lower = rel.lower()

        # Highest priority: Mentioned directly in stack trace / test failure
        for h in hint_files:
            if rel_lower.endswith(h) or h.endswith(rel_lower) or path.name.lower() == h:
                return 1

        # High priority: Test files
        if "test" in path.name.lower() or "tests" in rel_lower.split("/"):
            return 2

        # Medium priority: Core source files
        if rel_lower.startswith(("src/", "app/", "lib/")):
            return 3

        # Standard priority: Config / Python files
        if path.suffix == ".py":
            return 4
        if path.name in {"pyproject.toml", "setup.py", "setup.cfg"}:
            return 5

        return 6

    # Sort candidate files by priority
    sorted_files = sorted(all_files, key=score_file)

    source_files: dict[str, str] = {}
    test_files: dict[str, str] = {}

    current_bytes = len(bounded_stdout) + len(bounded_stderr) + len(tree)
    file_count = 0

    for path in sorted_files:
        if file_count >= settings.MAX_CONTEXT_FILES:
            break

        rel_path = str(path.relative_to(repo_root)).replace("\\", "/")

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # Bounded file content
        if len(content.encode("utf-8", errors="replace")) > settings.MAX_FILE_BYTES:
            content = content[: settings.MAX_FILE_BYTES] + "\n[... FILE CONTENT TRUNCATED ...]"

        file_bytes = len(content.encode("utf-8", errors="replace"))
        if current_bytes + file_bytes > settings.MAX_CONTEXT_BYTES:
            # Reached total context budget
            break

        # Categorize into test files vs source files
        if "test" in path.name.lower() or "tests" in rel_path.split("/"):
            test_files[rel_path] = content
        else:
            source_files[rel_path] = content

        current_bytes += file_bytes
        file_count += 1

    return RepositoryContext(
        tree=tree,
        source_files=source_files,
        test_files=test_files,
        traceback_hints=hints,
        stdout=bounded_stdout,
        stderr=bounded_stderr,
        total_bytes=current_bytes,
    )
