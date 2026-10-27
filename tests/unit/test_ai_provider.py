"""Unit tests for AI Provider abstractions (Mock & Nebius)."""

from __future__ import annotations

import pytest
from app.ai.client import MockAIProvider, NebiusAIProvider, create_ai_provider
from app.core.config import Settings


@pytest.mark.asyncio
async def test_mock_ai_provider():
    provider = MockAIProvider(model="test-nvidia-nemotron")
    response = await provider.generate(
        system_prompt="You are a test assistant.",
        user_prompt="Analyze this error log.",
    )
    assert response.provider == "mock"
    assert response.model == "test-nvidia-nemotron"
    assert "Defect verified" in response.content
    assert response.duration_ms > 0
    assert response.usage is not None
    assert response.usage.total_tokens > 0


def test_create_ai_provider_factory():
    # When no key configured, defaults to MockAIProvider
    settings_no_key = Settings(APP_ENV="test", NEBIUS_API_KEY="")
    provider = create_ai_provider(settings_no_key)
    assert isinstance(provider, MockAIProvider)

    # When key configured, produces NebiusAIProvider
    settings_with_key = Settings(
        APP_ENV="test",
        NEBIUS_API_KEY="test-key",
        NEBIUS_MODEL="nvidia/Nemotron-3_5-Lightning",
    )
    provider_nebius = create_ai_provider(settings_with_key)
    assert isinstance(provider_nebius, NebiusAIProvider)
    assert provider_nebius.model == "nvidia/Nemotron-3_5-Lightning"
