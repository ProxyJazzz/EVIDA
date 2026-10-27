"""Unit tests for configuration loading and validation."""

from __future__ import annotations

from app.core.config import Settings


def test_default_settings():
    settings = Settings(APP_ENV="test")
    assert settings.APP_NAME == "EVIDA"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.NEBIUS_BASE_URL == "https://api.tokenfactory.nebius.com/v1"
    assert settings.NEBIUS_MODEL == "nvidia/Nemotron-3_5-Lightning"
    assert settings.is_nebius_configured is False
    assert settings.is_supabase_configured is False


def test_custom_settings():
    settings = Settings(
        APP_ENV="production",
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="test-service-key",
        NEBIUS_API_KEY="test-nebius-key",
        NEBIUS_MODEL="nvidia/custom-model",
    )
    assert settings.is_supabase_configured is True
    assert settings.is_nebius_configured is True
    assert settings.NEBIUS_MODEL == "nvidia/custom-model"
