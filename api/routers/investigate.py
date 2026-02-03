"""POST /api/v1/investigate — main investigation endpoint."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, HTTPException

from api.models import InvestigateRequest, InvestigateResponse
from api.engine_adapter import build_ai_response_api

router = APIRouter()


@router.post("/investigate", response_model=InvestigateResponse)
def investigate(req: InvestigateRequest) -> InvestigateResponse:
    """Run the full investigation pipeline and return results."""
    payload = {
        "site": req.site,
        "tool_group": req.tool_group,
        "process_step": req.process_step,
        "severity": req.severity,
        "anomaly_summary": req.anomaly_summary,
        "timestamp": req.timestamp or dt.datetime.now().isoformat(),
        "metrics": req.metrics.model_dump(),
        "metrics_input_mode": "API",
    }

    try:
        response = build_ai_response_api(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    return response
