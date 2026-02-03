"""
Pydantic v2 response models for the AI pipeline.

Provides runtime validation of LLM outputs and structured types
for all data flowing through the pipeline.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.config import SITES, TOOL_GROUPS, PROCESS_STEPS, SEVERITY_LEVELS


# Lookup tables for case-insensitive config value matching (exclude placeholder "—" items)
_SITE_LOOKUP = {v.lower(): v for v in SITES[1:]}
_TOOL_GROUP_LOOKUP = {v.lower(): v for v in TOOL_GROUPS[1:]}
_PROCESS_STEP_LOOKUP = {v.lower(): v for v in PROCESS_STEPS[1:]}
_SEVERITY_LOOKUP_CFG = {v.lower(): v for v in SEVERITY_LEVELS[1:]}


class NLPExtractionResponse(BaseModel):
    """Validated shape of LLM field extraction from free-text input."""
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

    @field_validator("site", mode="before")
    @classmethod
    def normalize_site(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            matched = _SITE_LOOKUP.get(v.strip().lower())
            return matched  # None if not a valid config value
        return None

    @field_validator("tool_group", mode="before")
    @classmethod
    def normalize_tool_group(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            matched = _TOOL_GROUP_LOOKUP.get(v.strip().lower())
            return matched
        return None

    @field_validator("process_step", mode="before")
    @classmethod
    def normalize_process_step(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            matched = _PROCESS_STEP_LOOKUP.get(v.strip().lower())
            return matched
        return None

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            matched = _SEVERITY_LOOKUP_CFG.get(v.strip().lower())
            return matched
        return None


class Priority(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Confidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# Lookup tables for case-insensitive enum matching
_PRIORITY_LOOKUP = {v.value.lower(): v for v in Priority}
_CONFIDENCE_LOOKUP = {v.value.lower(): v for v in Confidence}


class NextCheck(BaseModel):
    category: str
    check: str
    why: str


class LLMInvestigationResponse(BaseModel):
    """Validated shape of the investigation LLM output."""
    narrative: str
    next_checks: list[NextCheck]
    escalation_summary: str


class LLMAssessmentResponse(BaseModel):
    """Validated shape of the assessment LLM output."""
    pattern: str
    priority: Priority
    confidence: Confidence
    diagnostic_approach: str
    reasoning: str

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v: str) -> str:
        if isinstance(v, str):
            matched = _PRIORITY_LOOKUP.get(v.strip().lower())
            if matched:
                return matched.value
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: str) -> str:
        if isinstance(v, str):
            matched = _CONFIDENCE_LOOKUP.get(v.strip().lower())
            if matched:
                return matched.value
        return v


class SimilarCaseDisplay(BaseModel):
    """Display-ready similar case after RAG retrieval."""
    case_id: str = ""
    family: str = ""
    similarity: str = "Low"
    similarity_score: str = ""
    matched_signals: str = ""
    resolution: str = ""


class PipelineTimings(BaseModel):
    """Millisecond-precision timing for each pipeline step."""
    rag_retrieval_ms: int = 0
    llm_generation_ms: int = 0
    llm_assessment_ms: int = 0
    total_ms: int = 0


class ResponseMeta(BaseModel):
    """Metadata attached to every pipeline response."""
    response_id: str
    backend: str
    model: str = ""
    rag_cases_retrieved: int = 0
    timings: PipelineTimings = Field(default_factory=PipelineTimings)
    llm_note: Optional[str] = None
