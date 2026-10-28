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
        self.fixed_response = fixed_response
        self._default_hypothesis_response = (
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
        self._default_regression_response = (
            "{\n"
            '  "test_path": "tests/test_regression.py",\n'
            '  "framework": "pytest",\n'
            '  "language": "python",\n'
            '  "description": "Verifies that divide(10, 2) returns 5 rather than multiplying operands to 20.",\n'
            '  "test_content": "from src.calculator import divide\\n\\ndef test_divide_regression():\\n    assert divide(10, 2) == 5\\n",\n'
            '  "target_symbol": "divide",\n'
            '  "target_file": "src/calculator.py",\n'
            '  "expected_failure_reason": "The implementation multiplies operands (*) instead of dividing (/), returning 20 instead of 5."\n'
            "}"
        )
        self._default_patch_response = (
            "{\n"
            '  "description": "Correct the divide function to perform mathematical division rather than multiplication.",\n'
            '  "patch_format": "unified_diff",\n'
            '  "patch_content": "--- a/src/calculator.py\\n+++ b/src/calculator.py\\n@@ -1,3 +1,3 @@\\n def divide(a: int, b: int) -> int:\\n     # Bug: multiplication instead of division\\n-    return a * b\\n+    return a / b\\n",\n'
            '  "changed_files": ["src/calculator.py"],\n'
            '  "change_summary": [\n'
            "    {\n"
            '      "file": "src/calculator.py",\n'
            '      "reason": "Replace incorrect multiplication operator (*) with division operator (/)."\n'
            "    }\n"
            "  ],\n"
            '  "reasoning": "The proven regression test and hypothesis show divide(10, 2) evaluates to 20 instead of 5 because multiplication was used instead of division."\n'
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
        if self.fixed_response is not None:
            content = self.fixed_response
        elif (
            "patch synthesis engine" in system_prompt.lower()
            or "patch generation" in system_prompt.lower()
            or "candidate patch" in system_prompt.lower()
        ):
            content = self._default_patch_response
        elif (
            "regression test generation engine" in system_prompt.lower()
            or "tests/test_regression.py" in system_prompt.lower()
        ):
            content = self._default_regression_response
        else:
            content = self._default_hypothesis_response

        return AIResponse(
            content=content,
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
    if settings.APP_ENV == "production":
        raise AIProviderError(
            "NEBIUS_API_KEY must be configured in production environment.",
            status_code=500,
        )
    return MockAIProvider(model=settings.NEBIUS_MODEL)
