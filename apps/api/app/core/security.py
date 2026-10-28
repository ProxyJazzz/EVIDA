"""Security and Authentication Helpers Module

Handles header inspection, tenant boundary extraction, and security exceptions.
"""

from __future__ import annotations

import uuid
from typing import NamedTuple

from fastapi import HTTPException, Request, status


class AuthCredentials(NamedTuple):
    user_id: str
    token: str


class SecurityException(HTTPException):
    def __init__(self, detail: str, code: str = "UNAUTHORIZED"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": code, "message": detail},
        )


def extract_bearer_token(request: Request) -> str | None:
    """Extract Authorization Bearer token from incoming request headers."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def get_current_user_id(request: Request) -> str:
    """Extract authenticated user ID for the current request.

    Checks Authorization Bearer token first, then X-User-Id header (for internal/proxy forwarding),
    falling back to local default tenant UID when in non-production.
    In production (APP_ENV == 'production'), an unauthenticated request raises SecurityException (401).
    """
    token = extract_bearer_token(request)
    if token:
        # Deterministically derive tenant UUID from token
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"evida-user-{token[:16]}"))

    x_user = request.headers.get("X-User-Id")
    if x_user:
        return x_user

    from app.core.config import get_settings

    settings = get_settings()
    if settings.APP_ENV == "production":
        raise SecurityException(
            "Authentication required. Provide a valid Authorization Bearer token.",
            code="UNAUTHORIZED",
        )

    # Return local test tenant UID
    return "00000000-0000-0000-0000-000000000001"
