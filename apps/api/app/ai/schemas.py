"""AI Provider Schemas"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AIResponse(BaseModel):
    content: str = Field(..., description="Generated text content from the AI model")
    model: str = Field(..., description="Model identifier used for generation")
    provider: str = Field(..., description="Provider name (e.g., 'nebius' or 'mock')")
    usage: TokenUsage | None = Field(default=None, description="Reported token counts")
    finish_reason: str | None = Field(default=None, description="Completion finish reason")
    duration_ms: float = Field(..., description="Request duration in milliseconds")
