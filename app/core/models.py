"""
Pydantic v2 response models for the AI pipeline.

Provides runtime validation of LLM outputs and structured types
for all data flowing through the pipeline.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


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
