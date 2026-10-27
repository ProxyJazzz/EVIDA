"""Supabase Service Client

Provides server-side Supabase client initialization using service-role credentials.
Designed to degrade gracefully when credentials are not configured during development.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger("evida.services.supabase")


class SupabaseClientService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._configured = settings.is_supabase_configured
        self.url = settings.SUPABASE_URL
        self.service_role_key = settings.SUPABASE_SERVICE_ROLE_KEY

    @property
    def is_configured(self) -> bool:
        return self._configured

    async def get_investigations_for_user(self, user_id: str) -> list[dict[str, Any]]:
        """Placeholder query for tenant investigations."""
        if not self._configured:
            logger.info("Supabase not configured, returning empty list")
            return []
        # When live Supabase client is connected (Phase 1), queries will run here
        return []
