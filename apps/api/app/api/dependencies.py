"""FastAPI Dependency Injection Providers"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.ai.client import AIProvider, create_ai_provider
from app.core.config import Settings, get_settings
from app.core.security import get_current_user_id
from app.domain.investigations.repository import get_investigation_repository
from app.domain.investigations.service import InvestigationService
from app.services.supabase import SupabaseClientService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_ai_provider_dep(settings: SettingsDep) -> AIProvider:
    return create_ai_provider(settings)


AIProviderDep = Annotated[AIProvider, Depends(get_ai_provider_dep)]


def get_supabase_service_dep(settings: SettingsDep) -> SupabaseClientService:
    return SupabaseClientService(settings)


SupabaseServiceDep = Annotated[SupabaseClientService, Depends(get_supabase_service_dep)]


def get_user_id_dep(request: Request) -> str:
    return get_current_user_id(request)


UserIdDep = Annotated[str, Depends(get_user_id_dep)]


def get_investigation_service_dep(settings: SettingsDep) -> InvestigationService:
    repo = get_investigation_repository(settings)
    return InvestigationService(repo)


InvestigationServiceDep = Annotated[InvestigationService, Depends(get_investigation_service_dep)]
