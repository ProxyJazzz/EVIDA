"""Worker Job Runner

Dispatches execution jobs to the isolated sandbox boundary.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path to import sandbox runner if needed
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SANDBOX_PATH = PROJECT_ROOT / "sandbox"
if str(SANDBOX_PATH) not in sys.path:
    sys.path.insert(0, str(SANDBOX_PATH))

from runner.runner import execute_command  # noqa: E402

from app.domain.verification.models import ExecutionResult  # noqa: E402
from app.workers.jobs import SandboxJob  # noqa: E402


class JobRunner:
    def __init__(self, default_timeout_seconds: float = 60.0) -> None:
        self.default_timeout = default_timeout_seconds

    async def execute_job(self, job: SandboxJob) -> ExecutionResult:
        """Execute a sandbox job and return the typed ExecutionResult."""
        timeout = job.timeout_seconds or self.default_timeout
        raw_result = execute_command(job.command, timeout_seconds=timeout)

        return ExecutionResult(
            exit_code=raw_result.exit_code,
            stdout=raw_result.stdout,
            stderr=raw_result.stderr,
            duration_ms=raw_result.duration_ms,
            timed_out=raw_result.timed_out,
            command=raw_result.command,
        )
