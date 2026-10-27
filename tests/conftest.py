"""Pytest Global Fixtures and Configuration"""

from __future__ import annotations

import pytest
import pytest_asyncio
from app.core.config import Settings
from app.main import create_app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing clean settings for testing."""
    return Settings(
        APP_ENV="test",
        APP_NAME="EVIDA",
        APP_VERSION="0.1.0",
        NEBIUS_MODEL="nvidia/Nemotron-3_5-Lightning",
    )


@pytest_asyncio.fixture
async def async_client():
    """Async client connected to the FastAPI application for testing."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
