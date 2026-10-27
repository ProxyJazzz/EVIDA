"""Reproduction Command Validator

Validates untrusted reproduction commands, restricting execution to supported
testing frameworks (pytest/python) and blocking dangerous shell characters.
"""

from __future__ import annotations

import shlex

from app.domain.investigations.state_machine import LifecycleException

# Permitted base executables
ALLOWED_EXECUTABLES = {"pytest", "python", "python3"}

# Disallowed shell metacharacters and tokens
FORBIDDEN_CHARACTERS = {";", "&", "|", ">", "<", "$", "`", "\\", "\n", "\r", "(", ")", "{", "}"}
FORBIDDEN_COMMANDS = {
    "sudo",
    "rm",
    "chmod",
    "chown",
    "curl",
    "wget",
    "nc",
    "netcat",
    "bash",
    "sh",
    "zsh",
    "eval",
    "exec",
    "su",
    "apt",
    "apk",
    "yum",
}


class CommandValidationError(LifecycleException):
    """Raised when an untrusted command violates execution policy."""

    def __init__(
        self, message: str, code: str = "INVALID_REPRODUCTION_COMMAND", status_code: int = 400
    ) -> None:
        super().__init__(message=message, code=code, status_code=status_code)


def validate_reproduction_command(command: str) -> list[str]:
    """Parse and validate untrusted reproduction command into structured arguments.

    Returns:
        Structured argument list safe for subprocess execution without shell=True.

    Raises:
        CommandValidationError: If command contains forbidden tokens or unsupported executables.
    """
    if not command or not command.strip():
        raise CommandValidationError("Reproduction command cannot be empty.")

    # Check for forbidden shell metacharacters
    for char in FORBIDDEN_CHARACTERS:
        if char in command:
            raise CommandValidationError(
                f"Command contains disallowed shell character: '{char}'.",
                code="EXECUTION_POLICY_BLOCKED",
                status_code=400,
            )

    try:
        args = shlex.split(command)
    except ValueError as exc:
        raise CommandValidationError(
            f"Failed to parse reproduction command: {exc}",
            code="INVALID_REPRODUCTION_COMMAND",
        ) from exc

    if not args:
        raise CommandValidationError("Reproduction command cannot be empty.")

    for arg in args[1:]:
        if ".." in arg:
            raise CommandValidationError(
                f"Path traversal in command argument is not permitted: '{arg}'.",
                code="EXECUTION_POLICY_BLOCKED",
                status_code=400,
            )

    executable = args[0].lower()

    # Block forbidden commands
    if executable in FORBIDDEN_COMMANDS:
        raise CommandValidationError(
            f"Execution of '{executable}' is blocked by sandbox policy.",
            code="EXECUTION_POLICY_BLOCKED",
            status_code=400,
        )

    # Check against allowed executables
    if executable not in ALLOWED_EXECUTABLES:
        raise CommandValidationError(
            f"Command executable '{executable}' is not allowed. Supported: {sorted(ALLOWED_EXECUTABLES)}.",
            code="INVALID_REPRODUCTION_COMMAND",
        )

    # If python is used, verify it's running a module or script, not inline code with arbitrary args
    if executable in {"python", "python3"}:
        if len(args) < 2:
            raise CommandValidationError(
                "Python command must specify a script or module (e.g., 'python -m pytest ...')."
            )
        # Block -c (inline execution) for untrusted input
        if "-c" in args:
            raise CommandValidationError(
                "Inline python execution ('-c') is blocked by sandbox policy.",
                code="EXECUTION_POLICY_BLOCKED",
                status_code=400,
            )

    return args
