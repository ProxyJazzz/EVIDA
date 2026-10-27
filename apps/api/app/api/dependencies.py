"""FastAPI Dependency Injection Providers"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.ai.client import AIProvider, create_ai_provider
from app.core.config import Settings, get_settings
from app.core.security import get_current_user_id
from app.domain.investigations.ai_service import AIInvestigationService
from app.domain.investigations.regression_service import RegressionService
from app.domain.investigations.repository import get_investigation_repository
from app.domain.investigations.service import InvestigationService
from app.domain.repositories.reproduction_service import ReproductionService
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


def get_reproduction_service_dep(
    settings: SettingsDep,
    investigation_service: InvestigationServiceDep,
) -> ReproductionService:
    repo = get_investigation_repository(settings)
    return ReproductionService(repo, investigation_service, settings)


ReproductionServiceDep = Annotated[ReproductionService, Depends(get_reproduction_service_dep)]


def get_ai_investigation_service_dep(
    settings: SettingsDep,
    investigation_service: InvestigationServiceDep,
    ai_provider: AIProviderDep,
) -> AIInvestigationService:
    repo = get_investigation_repository(settings)
    return AIInvestigationService(repo, investigation_service, ai_provider, settings)


AIInvestigationServiceDep = Annotated[
    AIInvestigationService, Depends(get_ai_investigation_service_dep)
]


def get_regression_service_dep(
    settings: SettingsDep,
    investigation_service: InvestigationServiceDep,
    ai_provider: AIProviderDep,
) -> RegressionService:
    repo = get_investigation_repository(settings)
    return RegressionService(repo, investigation_service, ai_provider, settings)


RegressionServiceDep = Annotated[RegressionService, Depends(get_regression_service_dep)]
