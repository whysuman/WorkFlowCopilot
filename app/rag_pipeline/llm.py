"""
LLM integration with multi-backend support.

Backends (priority order):
  1. HuggingFace Inference API (requires HF_TOKEN env var)
  2. Ollama local server (requires Ollama running on localhost:11434)
  3. Placeholder fallback (no external dependencies)

All generation functions return None on any failure, allowing the
orchestrator (engine.py) to fall through to the next backend.

Resilience features:
  - Tenacity retry with exponential backoff on transient failures
  - HuggingFace JSON mode (response_format=json_object)
  - Pydantic v2 validation of LLM outputs
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import (
    HF_MODEL,
    OLLAMA_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    LLM_TIMEOUT,
    LLM_MAX_RETRIES,
    LLM_RETRY_WAIT_MIN,
    LLM_RETRY_WAIT_MAX,
    SITES,
    TOOL_GROUPS,
    PROCESS_STEPS,
    SEVERITY_LEVELS,
)
from app.core.models import LLMInvestigationResponse, LLMAssessmentResponse, NLPExtractionResponse

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

def _check_huggingface_available() -> bool:
    """Check if HuggingFace Inference API is available (HF_TOKEN set + model responds)."""
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        return False
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(api_key=token)
        client.chat.completions.create(
            model=HF_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        return True
    except Exception:
        return False


def _check_ollama_available() -> bool:
    """Check if Ollama server is running AND the required model is pulled."""
    try:
        import httpx
        resp = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        return any(OLLAMA_MODEL in name for name in model_names)
    except Exception:
        return False


def detect_backend() -> str:
    """
    Detect the best available LLM backend.
    Returns: 'huggingface', 'ollama', or 'placeholder'
    """
    if _check_huggingface_available():
        return "huggingface"
    if _check_ollama_available():
        return "ollama"
    return "placeholder"


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_INVESTIGATION_SYSTEM_PROMPT = (
    "You are a semiconductor manufacturing investigation copilot. "
    "You provide DECISION-SUPPORT ONLY. You must NEVER claim root causes. "
    "You must NEVER invent checks or data not grounded in the provided context. "
    "Your role is to synthesize the current investigation signals with similar "
    "historical cases to help the engineer decide what to check next.\n\n"
    "IMPORTANT: Explain everything in clear, non-technical language that a "
    "non-specialist could understand. Avoid jargon — use plain English.\n\n"
    "Respond in this exact JSON format:\n"
    "{\n"
    '  "narrative": "A 3-5 sentence synthesis of what the signals suggest, '
    'referencing similar cases. Use plain language.",\n'
    '  "next_checks": [\n'
    '    {"category": "...", "check": "...", "why": "..."},\n'
    '    {"category": "...", "check": "...", "why": "..."}\n'
    "  ],\n"
    '  "escalation_summary": "A structured escalation summary with: observed, '
    'context, evidence, missing info, recommendation."\n'
    "}\n\n"
    "IMPORTANT: Return ONLY valid JSON. No markdown, no explanation outside the JSON."
)

_ASSESSMENT_SYSTEM_PROMPT = (
    "You are an investigation assessment engine for semiconductor manufacturing. "
    "You help engineers understand what type of problem they are dealing with "
    "and what diagnostic approach to take. Base your assessment on the investigation "
    "details and similar historical cases.\n\n"
    "Use plain, non-technical language in your reasoning and approach.\n\n"
    "Respond in this exact JSON format:\n"
    "{\n"
    '  "pattern": "The diagnostic pattern (e.g. Measurement Problem, Machine-Specific Issue, '
    "Gradual Drift, Configuration Change Impact, False Alarm, Hidden Quality Issue, "
    "Batch-to-Batch Variation, Signal-to-Noise Problem, Critical Machine Failure, "
    'Wear and Degradation, or Unknown)",\n'
    '  "priority": "one of: Critical, High, Medium, Low",\n'
    '  "confidence": "one of: High, Medium, Low — based on how much data is available",\n'
    '  "diagnostic_approach": "1-2 sentences in plain English: what the engineer should check first and why.",\n'
    '  "reasoning": "One sentence explaining the assessment in plain language."\n'
    "}\n\n"
    "IMPORTANT: Return ONLY valid JSON."
)


def _format_investigation_context(
    payload: Dict[str, Any],
    similar_cases: List[Tuple[Dict[str, Any], float]],
) -> str:
    """Build the user-facing context string for the LLM prompt."""
    metrics = payload.get("metrics", {})

    investigation = (
        "## Current Investigation\n"
        f"- Facility: {payload.get('site', 'unknown')}\n"
        f"- Machine Group: {payload.get('tool_group', 'unknown')}\n"
        f"- Manufacturing Step: {payload.get('process_step', 'unknown')}\n"
        f"- Severity: {payload.get('severity', 'unknown')}\n"
        f"- Issue Description: {payload.get('anomaly_summary', 'Not provided')}\n"
        f"- Metrics: {json.dumps({k: v for k, v in metrics.items() if v is not None}, indent=2)}\n"
    )

    cases_section = "\n## Similar Historical Cases (retrieved via semantic search)\n"
    for i, (case, score) in enumerate(similar_cases, 1):
        ctx = case.get("context", {})
        cases_section += (
            f"\n### Case {i} (similarity: {score:.2f})\n"
            f"- Family: {case.get('family', '')}\n"
            f"- Context: site={ctx.get('site', '')}, tool={ctx.get('tool_group', '')}, "
            f"step={ctx.get('process_step', '')}\n"
            f"- Key signals: {case.get('matched_signals_template', '')}\n"
            f"- Resolution: {case.get('resolution_summary', '')}\n"
            f"- Recommended checks: {', '.join(case.get('next_checks_hint', []))}\n"
        )

    return investigation + cases_section


def _format_triage_context(
    payload: Dict[str, Any],
    similar_cases: List[Tuple[Dict[str, Any], float]],
) -> str:
    """Build context string for triage classification."""
    metrics = payload.get("metrics", {})

    context = (
        f"Facility: {payload.get('site')}, Machine Group: {payload.get('tool_group')}, "
        f"Manufacturing Step: {payload.get('process_step')}, Severity: {payload.get('severity')}\n"
        f"Issue Description: {payload.get('anomaly_summary', 'Not provided')}\n"
        f"Metrics: {json.dumps({k: v for k, v in metrics.items() if v is not None})}\n"
    )

    if similar_cases:
        case, score = similar_cases[0]
        context += (
            f"\nTop similar case (score={score:.2f}): "
            f"Family='{case.get('family', '')}', "
            f"Resolution='{case.get('resolution_summary', '')}'"
        )

    return context


# ---------------------------------------------------------------------------
# JSON extraction helper
# ---------------------------------------------------------------------------

def _extract_json(raw: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from LLM output, handling markdown code fences."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        raw = "\n".join(lines).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# HuggingFace backend (with retry + JSON mode)
# ---------------------------------------------------------------------------

@retry(
    stop=stop_after_attempt(LLM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=LLM_RETRY_WAIT_MIN, max=LLM_RETRY_WAIT_MAX),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_huggingface(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Call HuggingFace Inference API with retry and JSON mode. Returns raw text or None."""
    from huggingface_hub import InferenceClient
    token = os.environ.get("HF_TOKEN", "")
    client = InferenceClient(api_key=token)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = client.chat.completions.create(
        model=HF_MODEL,
        messages=messages,
        max_tokens=LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Ollama backend (with retry)
# ---------------------------------------------------------------------------

@retry(
    stop=stop_after_attempt(LLM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=LLM_RETRY_WAIT_MIN, max=LLM_RETRY_WAIT_MAX),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_ollama(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Call local Ollama server via HTTP API with retry. Returns raw text or None."""
    import httpx
    response = httpx.post(
        "http://localhost:11434/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": LLM_TEMPERATURE, "num_predict": LLM_MAX_TOKENS},
            "stream": False,
        },
        timeout=LLM_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _call_backend(system_prompt: str, user_prompt: str, backend: str) -> Optional[str]:
    """Route to the appropriate backend. Catches all exceptions after retries exhaust."""
    try:
        if backend == "huggingface":
            return _call_huggingface(system_prompt, user_prompt)
        elif backend == "ollama":
            return _call_ollama(system_prompt, user_prompt)
    except Exception as e:
        logger.warning("%s call failed after retries: %s", backend, e)
    return None


def generate_llm_response(
    payload: Dict[str, Any],
    similar_cases: List[Tuple[Dict[str, Any], float]],
    backend: str,
) -> Optional[Dict[str, Any]]:
    """
    Generate narrative, next checks, and escalation summary via LLM.
    Returns Pydantic-validated dict or None on any failure.
    """
    if backend == "placeholder":
        return None

    user_prompt = _format_investigation_context(payload, similar_cases)
    raw = _call_backend(_INVESTIGATION_SYSTEM_PROMPT, user_prompt, backend)
    if raw is None:
        return None

    parsed = _extract_json(raw)
    if parsed is None:
        logger.warning("LLM response was not valid JSON")
        return None

    try:
        validated = LLMInvestigationResponse(**parsed)
        return validated.model_dump(mode="json")
    except ValidationError as e:
        logger.warning("LLM investigation response failed validation: %s", e)
        return None


def assess_investigation_llm(
    payload: Dict[str, Any],
    similar_cases: List[Tuple[Dict[str, Any], float]],
    backend: str,
) -> Optional[Dict[str, str]]:
    """
    Use LLM to assess the investigation for the engineer.
    Returns Pydantic-validated dict with pattern, priority, confidence,
    diagnostic_approach, reasoning — or None on failure.
    """
    if backend == "placeholder":
        return None

    user_prompt = _format_triage_context(payload, similar_cases)
    raw = _call_backend(_ASSESSMENT_SYSTEM_PROMPT, user_prompt, backend)
    if raw is None:
        return None

    parsed = _extract_json(raw)
    if parsed is None:
        logger.warning("LLM assessment response was not valid JSON")
        return None

    try:
        validated = LLMAssessmentResponse(**parsed)
        return validated.model_dump(mode="json")
    except ValidationError as e:
        logger.warning("LLM assessment response failed validation: %s", e)
        return None


# ---------------------------------------------------------------------------
# NLP free-text field extraction
# ---------------------------------------------------------------------------

_EXTRACTION_SYSTEM_PROMPT = (
    "You are a structured data extractor for semiconductor manufacturing investigations. "
    "Given a free-text description of a manufacturing issue, extract as many fields as possible "
    "into the JSON format below. Only include fields you are confident about from the text. "
    "Use null for any field not mentioned or unclear.\n\n"
    "Valid values for categorical fields:\n"
    f"- site: one of {SITES[1:]}\n"
    f"- tool_group: one of {TOOL_GROUPS[1:]}\n"
    f"- process_step: one of {PROCESS_STEPS[1:]}\n"
    f"- severity: one of {SEVERITY_LEVELS[1:]}\n\n"
    "Respond in this exact JSON format:\n"
    "{\n"
    '  "site": "string or null",\n'
    '  "tool_group": "string or null",\n'
    '  "process_step": "string or null",\n'
    '  "severity": "string or null",\n'
    '  "anomaly_summary": "string or null — a concise summary of the issue",\n'
    '  "yield_pct": number or null,\n'
    '  "metric_variance": number or null,\n'
    '  "change_magnitude": number or null,\n'
    '  "measurement_confidence": number or null,\n'
    '  "affected_lot_count": integer or null,\n'
    '  "rework_rate": number or null,\n'
    '  "time_window_hours": integer or null\n'
    "}\n\n"
    "IMPORTANT: Return ONLY valid JSON. No markdown, no explanation outside the JSON."
)


def extract_fields_from_text(free_text: str, backend: str) -> Optional[Dict[str, Any]]:
    """
    Extract structured investigation fields from free-text using an LLM.
    Returns Pydantic-validated dict or None on failure.
    Requires an LLM backend — returns None for 'placeholder'.
    """
    if backend == "placeholder":
        return None

    raw = _call_backend(_EXTRACTION_SYSTEM_PROMPT, free_text, backend)
    if raw is None:
        return None

    parsed = _extract_json(raw)
    if parsed is None:
        logger.warning("NLP extraction response was not valid JSON")
        return None

    try:
        validated = NLPExtractionResponse(**parsed)
        return validated.model_dump(mode="json")
    except ValidationError as e:
        logger.warning("NLP extraction response failed validation: %s", e)
        return None
