#!/usr/bin/env python3
"""EVIDA Sandbox Runner

Executes controlled commands in an isolated execution boundary with hard
timeouts, output size limits, and secret scrubbing.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any

# Sensitive environment variable keys that must NEVER leak into sandbox processes
SENSITIVE_ENV_KEYS = {
    "NEBIUS_API_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_ANON_KEY",
    "GITHUB_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "DATABASE_URL",
}

DEFAULT_TIMEOUT_SECONDS = 60.0
MAX_OUTPUT_BYTES = 1024 * 1024  # 1 MB


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sanitize_environment() -> dict[str, str]:
    """Build a sanitized environment copy stripped of sensitive credentials."""
    clean_env: dict[str, str] = {}
    for k, v in os.environ.items():
        if k not in SENSITIVE_ENV_KEYS and not k.startswith("SECRET_"):
            clean_env[k] = v

    clean_env["EVIDA_SANDBOX"] = "1"
    clean_env["PYTHONUNBUFFERED"] = "1"
    # Ensure current Python environment tools (like pytest) are discovered
    venv_bin = str(sys.executable.rsplit("/", 1)[0]) if "/" in sys.executable else ""
    current_path = clean_env.get("PATH", "")
    if venv_bin:
        clean_env["PATH"] = f"{venv_bin}:{current_path}" if current_path else venv_bin
    return clean_env


def execute_command(
    command: str | list[str],
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> SandboxResult:
    """Execute a controlled command with hard timeout and output size boundaries.

    Args:
        command: Command string or argument list to execute.
        timeout_seconds: Maximum wall-clock duration before SIGKILL.
        cwd: Working directory (defaults to current directory).
        env: Optional custom environment dictionary.

    Returns:
        SandboxResult with exit_code, stdout, stderr, duration_ms, and timeout status.
    """
    if isinstance(command, str):
        cmd_args = shlex.split(command)
        cmd_str = command
    else:
        cmd_args = list(command)
        cmd_str = " ".join(shlex.quote(c) for c in command)

    run_env = sanitize_environment() if env is None else env.copy()

    start_time = time.perf_counter()
    try:
        process = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=run_env,
            text=True,
            bufsize=1,
        )

        try:
            stdout_data, stderr_data = process.communicate(timeout=timeout_seconds)
            exit_code = process.returncode
            timed_out = False
        except subprocess.TimeoutExpired:
            process.kill()
            stdout_data, stderr_data = process.communicate()
            exit_code = 124  # Standard GNU timeout exit code
            timed_out = True

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Truncate if output exceeds size limit
        if len(stdout_data.encode("utf-8", errors="replace")) > MAX_OUTPUT_BYTES:
            stdout_data = (
                stdout_data[:MAX_OUTPUT_BYTES]
                + "\n[OUTPUT TRUNCATED: Exceeded 1MB limit]"
            )
        if len(stderr_data.encode("utf-8", errors="replace")) > MAX_OUTPUT_BYTES:
            stderr_data = (
                stderr_data[:MAX_OUTPUT_BYTES]
                + "\n[OUTPUT TRUNCATED: Exceeded 1MB limit]"
            )

        return SandboxResult(
            exit_code=exit_code,
            stdout=stdout_data,
            stderr=stderr_data,
            duration_ms=elapsed_ms,
            timed_out=timed_out,
            command=cmd_str,
        )

    except Exception as exc:  # noqa: BLE001
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return SandboxResult(
            exit_code=-1,
            stdout="",
            stderr=f"Sandbox Execution Error: {exc}",
            duration_ms=elapsed_ms,
            timed_out=False,
            command=cmd_str,
        )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: runner.py <command> [timeout_seconds]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_TIMEOUT_SECONDS

    result = execute_command(cmd, timeout_seconds=timeout)
    print(json.dumps(result.to_dict(), indent=2))
    sys.exit(result.exit_code)


if __name__ == "__main__":
    main()
