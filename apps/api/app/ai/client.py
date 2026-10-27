"""AI Provider Abstraction and Nebius Client

Provides a protocol-based AI provider interface with implementations for
Nebius Token Factory (targeting NVIDIA open models) and a deterministic Mock
provider for testing.
"""

from __future__ import annotations

import time
from typing import Any, Protocol

import httpx

from app.ai.schemas import AIResponse, TokenUsage
from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger("evida.ai.client")


class AIProviderError(Exception):
    """Base exception for AI provider operations."""

    def __init__(self, message: str, status_code: int | None = None, details: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class AIProvider(Protocol):
    """Core protocol defining the interface for AI inference providers."""

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AIResponse:
        """Generate a response using the configured model."""
        ...


class NebiusAIProvider:
    """Nebius Token Factory provider executing NVIDIA open-source models.

    Communicates via the OpenAI-compatible chat completions endpoint.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.tokenfactory.nebius.com/v1",
        model: str = "nvidia/Nemotron-3_5-Lightning",
        timeout_seconds: float = 60.0,
    ) -> None:
        self.api_key = api_key
        # Strip trailing slash from base_url
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout_seconds

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AIResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if response.status_code != 200:
                logger.error(
                    "Nebius API request failed",
                    extra={
                        "operation": "nebius_generate",
                        "status": "error",
                        "duration_ms": elapsed_ms,
                        "details": f"HTTP {response.status_code}",
                    },
                )
                raise AIProviderError(
                    f"Nebius request failed with status {response.status_code}: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()
            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")
            finish_reason = choice.get("finish_reason")

            usage_data = data.get("usage", {})
            usage = (
                TokenUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                )
                if usage_data
                else None
            )

            logger.info(
                "Nebius generation succeeded",
                extra={
                    "operation": "nebius_generate",
                    "status": "ok",
                    "duration_ms": elapsed_ms,
                },
            )

            return AIResponse(
                content=content,
                model=self.model,
                provider="nebius",
                usage=usage,
                finish_reason=finish_reason,
                duration_ms=elapsed_ms,
            )

        except httpx.TimeoutException as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            raise AIProviderError(f"Nebius request timed out after {self.timeout}s: {exc}") from exc
        except httpx.RequestError as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            raise AIProviderError(f"Nebius network connection error: {exc}") from exc


class MockAIProvider:
    """Mock AI Provider for unit tests and local offline development."""

    def __init__(
        self,
        model: str = "mock-nvidia-nemotron",
        fixed_response: str | None = None,
    ) -> None:
        self.model = model
        self.fixed_response = fixed_response or (
            "{\n"
            '  "hypothesis": "Defect verified: The divide function multiplies its operands instead of dividing.",\n'
            '  "confidence": 0.99,\n'
            '  "root_cause": {\n'
            '    "file": "src/calculator.py",\n'
            '    "symbol": "divide",\n'
            '    "line": 4,\n'
            '    "description": "Defect verified: The implementation uses multiplication (*) instead of division (/)." \n'
            "  },\n"
            '  "affected_files": ["src/calculator.py"],\n'
            '  "evidence": [\n'
            '    "The reproduction test expects 5 but the function returns 20.",\n'
            '    "The reproduction command exited with code 1."\n'
            "  ],\n"
            '  "recommended_next_action": "generate_regression_test"\n'
            "}"
        )

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AIResponse:
        return AIResponse(
            content=self.fixed_response,
            model=self.model,
            provider="mock",
            usage=TokenUsage(prompt_tokens=42, completion_tokens=84, total_tokens=126),
            finish_reason="stop",
            duration_ms=5.0,
        )


def create_ai_provider(settings: Settings) -> AIProvider:
    """Factory creating configured AI provider (Nebius or Mock)."""
    if settings.is_nebius_configured and settings.NEBIUS_API_KEY:
        return NebiusAIProvider(
            api_key=settings.NEBIUS_API_KEY,
            base_url=settings.NEBIUS_BASE_URL,
            model=settings.NEBIUS_MODEL,
            timeout_seconds=settings.AI_REQUEST_TIMEOUT_SECONDS,
        )
    return MockAIProvider(model=settings.NEBIUS_MODEL)
