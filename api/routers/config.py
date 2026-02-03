"""GET /api/v1/config — dropdown options for Power Apps."""
from __future__ import annotations

from fastapi import APIRouter

from api.models import ConfigResponse
from app.config import SITES, TOOL_GROUPS, PROCESS_STEPS, SEVERITY_LEVELS

router = APIRouter()


@router.get("/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    """Return dropdown options stripped of placeholder items."""
    return ConfigResponse(
        sites=SITES[1:],
        tool_groups=TOOL_GROUPS[1:],
        process_steps=PROCESS_STEPS[1:],
        severity_levels=SEVERITY_LEVELS[1:],
    )
