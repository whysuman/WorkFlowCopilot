"""GET /api/v1/health — health check with RAG/LLM status."""
from __future__ import annotations

from fastapi import APIRouter

from api.models import HealthResponse
from api.engine_adapter import is_rag_loaded
from app.rag_pipeline.llm import detect_backend

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        rag_loaded=is_rag_loaded(),
        llm_backend=detect_backend(),
    )
