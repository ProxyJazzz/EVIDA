"""Investigation Service Interface

Coordinates between repository ingestion, sandbox failure reproduction,
and AI hypothesis generation.
"""

from __future__ import annotations

import json
from uuid import UUID

from app.ai.client import AIProvider
from app.ai.prompts import HYPOTHESIS_USER_PROMPT_TEMPLATE, INVESTIGATION_SYSTEM_PROMPT
from app.domain.investigations.models import InvestigationHypothesis


class InvestigatorService:
    def __init__(self, ai_provider: AIProvider) -> None:
        self.ai_provider = ai_provider

    async def investigate_issue(
        self,
        investigation_id: UUID,
        repo_name: str,
        issue_title: str,
        issue_description: str,
        traceback: str = "",
    ) -> InvestigationHypothesis:
        """Query AI provider for causal hypothesis based on failure evidence."""
        user_prompt = HYPOTHESIS_USER_PROMPT_TEMPLATE.format(
            repo_name=repo_name,
            issue_title=issue_title,
            issue_description=issue_description or "No description provided.",
            traceback=traceback or "No traceback provided.",
        )

        response = await self.ai_provider.generate(
            system_prompt=INVESTIGATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        try:
            data = json.loads(response.content)
            return InvestigationHypothesis(**data)
        except Exception:
            # Fallback if raw text returned
            return InvestigationHypothesis(
                summary=f"Analysis for: {issue_title}",
                root_cause=response.content[:200],
                affected_files=[],
                confidence=0.5,
                reproduction_strategy="Reproduce using synthetic test runner",
            )
