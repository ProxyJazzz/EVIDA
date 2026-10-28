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

    # Phase 2 Archive Ingestion and Reproduction Boundaries
    MAX_ARCHIVE_SIZE_MB: int = Field(default=50, description="Max allowed ZIP size in MB")
    MAX_EXTRACTED_SIZE_MB: int = Field(default=200, description="Max allowed extracted size in MB")
    MAX_FILE_COUNT: int = Field(default=5000, description="Max allowed file count in ZIP archive")
    MAX_SINGLE_FILE_SIZE_MB: int = Field(default=20, description="Max single file size in MB")
    REPRODUCTION_TIMEOUT_SECONDS: float = Field(
        default=30.0, description="Max execution timeout for reproduction runs"
    )
    STORAGE_DIR: str = Field(
        default=".evida_storage", description="Local storage root for uploaded archives"
    )

    # Phase 3 AI Investigation Context Limits
    MAX_CONTEXT_FILES: int = Field(default=20, description="Max files to include in AI context")
    MAX_CONTEXT_BYTES: int = Field(
        default=100000, description="Max total context size in bytes sent to AI"
    )
    MAX_FILE_BYTES: int = Field(
        default=20000, description="Max bytes per file included in AI context"
    )
    MAX_TREE_ENTRIES: int = Field(
        default=500, description="Max directory tree entries in repository view"
    )
    MAX_STDOUT_CONTEXT_BYTES: int = Field(
        default=20000, description="Max stdout bytes included in AI context"
    )
    MAX_STDERR_CONTEXT_BYTES: int = Field(
        default=20000, description="Max stderr bytes included in AI context"
    )
    INVESTIGATION_PROMPT_VERSION: str = Field(
        default="evida-investigation-v1",
        description="Canonical investigation prompt template version",
    )
    MAX_GENERATED_TEST_BYTES: int = Field(
        default=20000, description="Max allowed bytes for an AI-generated regression test"
    )
    REGRESSION_TEST_PROMPT_VERSION: str = Field(
        default="evida-regression-test-v1",
        description="Canonical regression test prompt template version",
    )

    # Phase 5 Patch Generation & Validation Boundaries
    MAX_GENERATED_PATCH_BYTES: int = Field(
        default=50000, description="Max allowed bytes for an AI-generated patch"
    )
    MAX_PATCH_FILES: int = Field(
        default=5, description="Max allowed changed files in a candidate patch"
    )
    MAX_PATCH_HUNKS: int = Field(
        default=20, description="Max allowed diff hunks in a candidate patch"
    )
    PATCH_GENERATION_PROMPT_VERSION: str = Field(
        default="evida-patch-generation-v1",
        description="Canonical patch generation prompt template version",
    )

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
