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
    """Extract or mock authenticated user ID for the current request.

    In Phase 0, if no Authorization header is present during local development,
    a deterministic anonymous session UID is provided for developer ergonomics.
    """
    token = extract_bearer_token(request)
    if token:
        # Phase 0 token extractor placeholder (validated via Supabase Auth in Phase 1)
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"evida-user-{token[:16]}"))

    # Return local test tenant UID
    return "00000000-0000-0000-0000-000000000001"
