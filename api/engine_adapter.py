"""
Streamlit-free wrapper around the RAG pipeline.
Replicates build_ai_response() logic from app/rag_pipeline/engine.py
without any Streamlit dependency.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from app.rag_pipeline.rag import load_cases, build_or_load_collection, retrieve_similar_cases
from app.rag_pipeline.llm import (
    detect_backend,
    generate_llm_response,
    assess_investigation_llm,
)
from app.rag_pipeline.triage import assess_investigation
from app.rag_pipeline.placeholder import build_placeholder_response
from app.config import CASES_PATH, HF_MODEL, OLLAMA_MODEL, MIN_SIMILARITY_SCORE

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons (replaces @st.cache_resource)
# ---------------------------------------------------------------------------

_cases: Optional[List[Dict[str, Any]]] = None
_collection: Optional[Any] = None
_response_cache: dict[str, Dict[str, Any]] = {}


def init_rag_pipeline() -> Tuple[Optional[List[Dict[str, Any]]], Optional[Any]]:
    """
    Initialize RAG pipeline once (module-level singleton).
    Loads cases and builds/loads the ChromaDB collection.
    Returns (cases, collection) or (None, None) on failure.
    """
    global _cases, _collection
    if _cases is not None and _collection is not None:
        return _cases, _collection
    try:
        _cases = load_cases(CASES_PATH)
        _collection = build_or_load_collection(_cases, CASES_PATH)
        logger.info("RAG pipeline initialized: %d cases loaded", len(_cases))
        return _cases, _collection
    except Exception as e:
        logger.warning("RAG pipeline initialization failed: %s", e)
        return None, None


def is_rag_loaded() -> bool:
    """Check if RAG pipeline is initialized."""
    return _cases is not None and _collection is not None


# ---------------------------------------------------------------------------
# Response cache
# ---------------------------------------------------------------------------

def _payload_hash(payload: Dict[str, Any]) -> str:
    """Deterministic hash of payload for cache key."""
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Main orchestration (mirrors engine.py without Streamlit)
# ---------------------------------------------------------------------------

def _format_retrieved_cases(
    retrieved: List[Tuple[Dict[str, Any], float]],
) -> List[Dict[str, str]]:
    """Convert RAG results into the display format."""
    display = []
    for case, score in retrieved:
        if score >= 0.85:
            sim_label = "High"
        elif score >= 0.65:
            sim_label = "Medium"
        else:
            sim_label = "Low"

        display.append({
            "case_id": case.get("case_id", ""),
            "family": case.get("family", ""),
            "similarity": sim_label,
            "similarity_score": f"{score:.2f}",
            "matched_signals": case.get("matched_signals_template", ""),
            "resolution": case.get("resolution_summary", ""),
        })
    return display


def build_ai_response_api(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main orchestration function for the API.
    Mirrors engine.py build_ai_response() without Streamlit.
    """
    # --- Cache check ---
    cache_key = _payload_hash(payload)
    if cache_key in _response_cache:
        cached = _response_cache[cache_key].copy()
        cached["meta"] = {**cached["meta"], "from_cache": True}
        return cached

    pipeline_start = time.perf_counter()
    timings: Dict[str, int] = {}

    # --- Step 1: RAG retrieval ---
    t0 = time.perf_counter()
    cases, collection = init_rag_pipeline()
    retrieved_cases: List[Tuple[Dict[str, Any], float]] = []
    rag_available = cases is not None and collection is not None

    if rag_available:
        try:
            filters = {
                "process_step": payload.get("process_step", ""),
                "site": payload.get("site", ""),
                "tool_group": payload.get("tool_group", ""),
            }
            retrieved_cases = retrieve_similar_cases(
                payload, cases, collection, top_k=3, filters=filters,
            )
            retrieved_cases = [
                (case, score) for case, score in retrieved_cases
                if score >= MIN_SIMILARITY_SCORE
            ]
        except Exception as e:
            logger.warning("RAG retrieval failed: %s", e)
            rag_available = False
    timings["rag_retrieval_ms"] = int((time.perf_counter() - t0) * 1000)

    # --- Step 2: Detect LLM backend ---
    backend = detect_backend()

    # --- Step 3: Attempt LLM generation ---
    t0 = time.perf_counter()
    llm_response = None
    if backend != "placeholder" and retrieved_cases:
        llm_response = generate_llm_response(payload, retrieved_cases, backend)
    timings["llm_generation_ms"] = int((time.perf_counter() - t0) * 1000)

    if llm_response is not None:
        narrative = llm_response.get("narrative", "")
        next_checks = llm_response.get("next_checks", [])
        escalation_summary = llm_response.get("escalation_summary", "")

        if len(next_checks) < 2:
            placeholder = build_placeholder_response(payload)
            next_checks = placeholder["next_checks"]

        similar_cases_display = _format_retrieved_cases(retrieved_cases)

        t0 = time.perf_counter()
        assessment = assess_investigation_llm(payload, retrieved_cases, backend)
        timings["llm_assessment_ms"] = int((time.perf_counter() - t0) * 1000)

        if assessment is None:
            assessment = assess_investigation(payload, retrieved_cases)
            assessment["source"] = "rules"
        else:
            assessment["source"] = "llm"

        timings["total_ms"] = int((time.perf_counter() - pipeline_start) * 1000)

        model_name = HF_MODEL if backend == "huggingface" else OLLAMA_MODEL
        response = {
            "similar_cases": similar_cases_display,
            "no_strong_match_note": None,
            "next_checks": next_checks,
            "escalation_summary": escalation_summary,
            "narrative": narrative,
            "assessment": assessment,
            "meta": {
                "response_id": f"resp_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "backend": backend,
                "model": model_name,
                "rag_cases_retrieved": len(retrieved_cases),
                "timings": timings,
            },
        }
        _response_cache[cache_key] = response
        return response

    # --- Step 4: Fallback path ---
    response = build_placeholder_response(payload)

    if retrieved_cases:
        response["similar_cases"] = _format_retrieved_cases(retrieved_cases)
        response["no_strong_match_note"] = None

    t0 = time.perf_counter()
    assessment = assess_investigation(payload, retrieved_cases or [])
    timings["llm_assessment_ms"] = int((time.perf_counter() - t0) * 1000)
    assessment["source"] = "rules"
    response["assessment"] = assessment

    timings["total_ms"] = int((time.perf_counter() - pipeline_start) * 1000)

    response["meta"]["backend"] = backend
    response["meta"]["rag_cases_retrieved"] = len(retrieved_cases)
    response["meta"]["timings"] = timings

    if backend == "placeholder":
        response["meta"]["llm_note"] = (
            "No LLM backend available. Set HF_TOKEN for HuggingFace API, "
            "or start Ollama for local inference."
        )

    _response_cache[cache_key] = response
    return response
