"""
AI Engine: orchestrates RAG retrieval, LLM generation, and investigation assessment.
Single entry point for the entire AI pipeline with graceful fallback.

Flow:
  1. RAG retrieval (always attempted)
  2. Detect LLM backend (HuggingFace -> Ollama -> placeholder)
  3. If LLM available: generate narrative + assessment via LLM
  4. If LLM unavailable: placeholder response + rule-based assessment
  5. Always includes: investigation assessment, response metadata
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from app.rag_pipeline.rag import load_cases, build_or_load_collection, retrieve_similar_cases
from app.rag_pipeline.llm import (
    detect_backend,
    generate_llm_response,
    assess_investigation_llm,
    OLLAMA_MODEL,
    HF_MODEL,
)
from app.rag_pipeline.triage import assess_investigation
from app.rag_pipeline.placeholder import build_placeholder_response
from app.config import CASES_PATH

@st.cache_resource
def init_rag_pipeline() -> Tuple[Optional[List[Dict[str, Any]]], Optional[Any]]:
    """
    Initialize RAG pipeline once (cached across Streamlit reruns).
    Loads cases and builds/loads the ChromaDB collection.
    Returns (cases, collection) or (None, None) on failure.
    """
    try:
        cases = load_cases(CASES_PATH)
        collection = build_or_load_collection(cases, CASES_PATH)
        return cases, collection
    except Exception as e:
        st.warning(f"RAG pipeline initialization failed: {e}")
        return None, None


def build_ai_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main orchestration function. Replaces build_placeholder_response().

    Returns a response dict compatible with render_outputs().
    """
    # --- Step 1: RAG retrieval ---
    cases, collection = init_rag_pipeline()
    retrieved_cases: List[Tuple[Dict[str, Any], float]] = []
    rag_available = cases is not None and collection is not None

    if rag_available:
        try:
            # Build metadata filters from payload context fields
            filters = {
                "process_step": payload.get("process_step", ""),
                "site": payload.get("site", ""),
                "tool_group": payload.get("tool_group", ""),
            }
            retrieved_cases = retrieve_similar_cases(
                payload, cases, collection, top_k=3, filters=filters,
            )
        except Exception as e:
            st.warning(f"RAG retrieval failed: {e}")
            rag_available = False

    # --- Step 2: Detect LLM backend ---
    backend = detect_backend()

    # --- Step 3: Attempt LLM generation ---
    llm_response = None
    if backend != "placeholder" and retrieved_cases:
        llm_response = generate_llm_response(payload, retrieved_cases, backend)

    if llm_response is not None:
        # LLM succeeded
        narrative = llm_response.get("narrative", "")
        next_checks = llm_response.get("next_checks", [])
        escalation_summary = llm_response.get("escalation_summary", "")

        # Ensure minimum 2 checks
        if len(next_checks) < 2:
            placeholder = build_placeholder_response(payload)
            next_checks = placeholder["next_checks"]

        similar_cases_display = _format_retrieved_cases(retrieved_cases)

        # Assessment via LLM
        assessment = assess_investigation_llm(payload, retrieved_cases, backend)
        if assessment is None:
            assessment = assess_investigation(payload, retrieved_cases)
            assessment["source"] = "rules"
        else:
            assessment["source"] = "llm"

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
            },
        }
        return response

    # --- Step 4: Fallback path ---
    response = build_placeholder_response(payload)

    # Still use RAG results for similar_cases if available
    if retrieved_cases:
        response["similar_cases"] = _format_retrieved_cases(retrieved_cases)
        response["no_strong_match_note"] = None

    # Rule-based assessment (always available)
    assessment = assess_investigation(payload, retrieved_cases or [])
    assessment["source"] = "rules"
    response["assessment"] = assessment

    response["meta"]["backend"] = backend
    response["meta"]["rag_cases_retrieved"] = len(retrieved_cases)

    if backend == "placeholder":
        response["meta"]["llm_note"] = (
            "No LLM backend available. Set HF_TOKEN for HuggingFace API, "
            "or start Ollama for local inference."
        )

    return response


def _format_retrieved_cases(
    retrieved: List[Tuple[Dict[str, Any], float]],
) -> List[Dict[str, str]]:
    """Convert RAG results into the display format expected by render_outputs()."""
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
