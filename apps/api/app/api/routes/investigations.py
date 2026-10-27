"""Investigation Routes (Foundation)"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import SupabaseServiceDep, UserIdDep
from app.domain.investigations.models import InvestigationListResponse

router = APIRouter(prefix="/investigations", tags=["Investigations"])


@router.get("", response_model=InvestigationListResponse)
async def list_investigations(
    user_id: UserIdDep,
    supabase: SupabaseServiceDep,
) -> InvestigationListResponse:
    """List investigations for the authenticated user."""
    items = await supabase.get_investigations_for_user(user_id)
    return InvestigationListResponse(
        items=[],  # Populated with live data in Phase 1
        total=len(items),
    )
