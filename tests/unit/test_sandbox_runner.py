"""Unit tests for Sandbox Runner."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure sandbox is on path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SANDBOX_PATH = PROJECT_ROOT / "sandbox"
if str(SANDBOX_PATH) not in sys.path:
    sys.path.insert(0, str(SANDBOX_PATH))

from runner.runner import execute_command, sanitize_environment


def test_sandbox_controlled_execution():
    result = execute_command(
        "python3 -c \"print('EVIDA sandbox OK')\"", timeout_seconds=10.0
    )
    assert result.exit_code == 0
    assert "EVIDA sandbox OK" in result.stdout
    assert result.timed_out is False
    assert result.duration_ms > 0


def test_sandbox_timeout_enforcement():
    # Execute a command that exceeds a 0.5s timeout
    result = execute_command(
        'python3 -c "import time; time.sleep(2)"', timeout_seconds=0.5
    )
    assert result.exit_code == 124
    assert result.timed_out is True
    assert result.duration_ms >= 450


def test_sandbox_environment_sanitization():
    clean_env = sanitize_environment()
    assert clean_env.get("EVIDA_SANDBOX") == "1"
    assert "NEBIUS_API_KEY" not in clean_env
    assert "SUPABASE_SERVICE_ROLE_KEY" not in clean_env
