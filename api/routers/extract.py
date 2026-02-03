"""POST /api/v1/extract — NLP free-text extraction endpoint."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.models import ExtractRequest, ExtractResponse
from app.rag_pipeline.llm import detect_backend, extract_fields_from_text

router = APIRouter()


@router.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest) -> ExtractResponse:
    """Extract structured investigation fields from free-text using an LLM."""
    backend = detect_backend()

    if backend == "placeholder":
        raise HTTPException(
            status_code=503,
            detail="NLP extraction requires an LLM backend. "
                   "Set HF_TOKEN or start Ollama.",
        )

    result = extract_fields_from_text(req.text, backend)
    if result is None:
        raise HTTPException(
            status_code=422,
            detail="Failed to extract fields from the provided text.",
        )

    return ExtractResponse(**result, backend=backend)
