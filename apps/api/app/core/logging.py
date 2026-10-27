"""Structured Application Logging Module

Provides JSON-formatted structured logging with context propagation (request_id,
user_id, investigation_id) and secret scrubbing to prevent accidental leakage.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variables for distributed tracing
ctx_request_id: ContextVar[str | None] = ContextVar("ctx_request_id", default=None)
ctx_user_id: ContextVar[str | None] = ContextVar("ctx_user_id", default=None)
ctx_investigation_id: ContextVar[str | None] = ContextVar("ctx_investigation_id", default=None)

# Patterns to scrub from log messages
SENSITIVE_PATTERNS = [
    re.compile(r"Bearer\s+([A-Za-z0-9_\-\.]+)", re.IGNORECASE),
    re.compile(r"ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"),  # JWT
    re.compile(r"(nebius_api_key|api_key|service_role_key|secret)=([^\s&]+)", re.IGNORECASE),
]


def scrub_secrets(text: str) -> str:
    """Mask credentials and tokens in log strings."""
    scrubbed = text
    for pattern in SENSITIVE_PATTERNS:
        scrubbed = pattern.sub(r"[REDACTED_CREDENTIAL]", scrubbed)
    return scrubbed


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as compact structured JSON with contextual metadata."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": scrub_secrets(record.getMessage()),
        }

        # Add trace context if present
        req_id = ctx_request_id.get()
        if req_id:
            log_payload["request_id"] = req_id

        user_id = ctx_user_id.get()
        if user_id:
            log_payload["user_id"] = user_id

        inv_id = ctx_investigation_id.get()
        if inv_id:
            log_payload["investigation_id"] = inv_id

        # Attach custom extra fields (operation, duration_ms, status)
        for key in ("operation", "duration_ms", "status", "details"):
            if hasattr(record, key):
                log_payload[key] = getattr(record, key)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def configure_logging(level: str = "INFO") -> None:
    """Initialize structured JSON logging for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(stream_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
