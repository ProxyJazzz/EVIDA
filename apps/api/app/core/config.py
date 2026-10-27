"""Application Configuration Module

Uses pydantic-settings to validate environment variables and provide typed
settings across the application.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application identity
    APP_ENV: Literal["development", "test", "production"] = "development"
    APP_NAME: str = "EVIDA"
    APP_VERSION: str = "0.1.0"

    # Server configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Supabase credentials (optional during offline dev/test)
    SUPABASE_URL: str | None = Field(default=None, description="Supabase project URL")
    SUPABASE_ANON_KEY: str | None = Field(default=None, description="Supabase anon key")
    SUPABASE_SERVICE_ROLE_KEY: str | None = Field(
        default=None, description="Supabase service role secret"
    )

    # Nebius Token Factory & NVIDIA Model
    NEBIUS_API_KEY: str | None = Field(default=None, description="Nebius Token Factory API key")
    NEBIUS_BASE_URL: str = Field(
        default="https://api.tokenfactory.nebius.com/v1",
        description="Nebius Token Factory base URL",
    )
    NEBIUS_MODEL: str = Field(
        default="nvidia/Nemotron-3_5-Lightning",
        description="Selected NVIDIA Open Model ID",
    )
    AI_REQUEST_TIMEOUT_SECONDS: float = Field(
        default=60.0, description="Nebius API timeout in seconds"
    )

    # Sandbox execution limits
    SANDBOX_TIMEOUT_SECONDS: float = Field(default=60.0, description="Sandbox run timeout")

    @property
    def is_supabase_configured(self) -> bool:
        """Return True if required Supabase credentials are provided."""
        return bool(
            self.SUPABASE_URL and (self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_ANON_KEY)
        )

    @property
    def is_nebius_configured(self) -> bool:
        """Return True if Nebius API key is configured."""
        return bool(self.NEBIUS_API_KEY and self.NEBIUS_API_KEY.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached instance of application settings."""
    return Settings()
