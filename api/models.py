"""
Pydantic request/response models for the FastAPI REST API.
Reuses core models from app.core.models where possible.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.core.models import NextCheck, SimilarCaseDisplay, PipelineTimings, ResponseMeta


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class MetricsInput(BaseModel):
    """Optional metric fields for an investigation request."""
    yield_pct: Optional[float] = None
    metric_variance: Optional[float] = None
    change_magnitude: Optional[float] = None
    measurement_confidence: Optional[float] = None
    affected_lot_count: Optional[int] = None
    rework_rate: Optional[float] = None
    time_window_hours: Optional[int] = None


class InvestigateRequest(BaseModel):
    """Maps 1:1 to build_ai_response() payload."""
    site: str = ""
    tool_group: str = ""
    process_step: str = ""
    severity: str = ""
    anomaly_summary: str = ""
    timestamp: Optional[str] = None
    metrics: MetricsInput = Field(default_factory=MetricsInput)


class ExtractRequest(BaseModel):
    """Free-text string for NLP extraction."""
    text: str


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class AssessmentResponse(BaseModel):
    """Investigation assessment output."""
    pattern: str = ""
    priority: str = ""
    confidence: str = ""
    diagnostic_approach: str = ""
    reasoning: str = ""
    source: str = ""


class InvestigateResponse(BaseModel):
    """Full pipeline response shape."""
    similar_cases: List[SimilarCaseDisplay] = Field(default_factory=list)
    no_strong_match_note: Optional[str] = None
    next_checks: List[NextCheck] = Field(default_factory=list)
    escalation_summary: str = ""
    narrative: str = ""
    assessment: AssessmentResponse = Field(default_factory=AssessmentResponse)
    meta: ResponseMeta


class ExtractResponse(BaseModel):
    """Extracted fields from NLP free-text."""
    site: Optional[str] = None
    tool_group: Optional[str] = None
    process_step: Optional[str] = None
    severity: Optional[str] = None
    anomaly_summary: Optional[str] = None
    yield_pct: Optional[float] = None
    metric_variance: Optional[float] = None
    change_magnitude: Optional[float] = None
    measurement_confidence: Optional[float] = None
    affected_lot_count: Optional[int] = None
    rework_rate: Optional[float] = None
    time_window_hours: Optional[int] = None
    backend: str = ""


class ConfigResponse(BaseModel):
    """Dropdown options for Power Apps."""
    sites: List[str]
    tool_groups: List[str]
    process_steps: List[str]
    severity_levels: List[str]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    rag_loaded: bool = False
    llm_backend: str = ""
