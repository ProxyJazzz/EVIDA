"""Health and Readiness Probes Route Handler"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.dependencies import SettingsDep

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "evida-api"
    version: str = "0.1.0"


class ReadinessCheckDetail(BaseModel):
    configured: bool
    provider: str
    model: str | None = None
    ready: bool | None = None
    runner: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    service: str
    version: str
    checks: dict[str, Any]


@router.get("", response_model=HealthResponse)
async def get_health(settings: SettingsDep) -> HealthResponse:
    """Liveness probe.

    Returns 200 OK immediately without requiring external dependencies.
    """
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME.lower() + "-api",
        version=settings.APP_VERSION,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def get_readiness(settings: SettingsDep) -> ReadinessResponse:
    """Readiness probe.

    Inspects external dependencies (database, AI inference provider, sandbox)
    and reports readiness. Remains operational in local development when
    optional services are not configured.
    """
    db_configured = settings.is_supabase_configured
    ai_configured = settings.is_nebius_configured

    checks = {
        "database": {
            "configured": db_configured,
            "provider": "supabase",
        },
        "ai_provider": {
            "configured": ai_configured,
            "provider": "nebius" if ai_configured else "mock",
            "model": settings.NEBIUS_MODEL,
        },
        "sandbox": {
            "ready": True,
            "runner": "isolated_process",
        },
    }

    # In development, report 'ready' even if external keys are optional
    # In production, check if required keys are present
    overall_status = "ready"
    if settings.APP_ENV == "production" and not (db_configured and ai_configured):
        overall_status = "not_ready"

    return ReadinessResponse(
        status=overall_status,
        service=settings.APP_NAME.lower() + "-api",
        version=settings.APP_VERSION,
        checks=checks,
    )
