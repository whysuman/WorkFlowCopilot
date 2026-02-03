"""
LLM integration with multi-backend support.

Backends (priority order):
  1. HuggingFace Inference API (requires HF_TOKEN env var)
  2. Ollama local server (requires Ollama running on localhost:11434)
  3. Placeholder fallback (no external dependencies)

All generation functions return None on any failure, allowing the
orchestrator (ai_engine.py) to fall through to the next backend.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

HF_MODEL = "Qwen/Qwen2.5-72B-Instruct:novita"
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_TIMEOUT = 60


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
        import ollama
        models_resp = ollama.list()
        model_names = [m.get("name", "") for m in getattr(models_resp, "models", [])]
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
# HuggingFace backend
# ---------------------------------------------------------------------------

def _call_huggingface(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Call HuggingFace Inference API. Returns raw text or None."""
    try:
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
            max_tokens=1024,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning("HuggingFace call failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Ollama backend
# ---------------------------------------------------------------------------

def _call_ollama(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Call local Ollama server. Returns raw text or None."""
    try:
        import ollama
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.3, "num_predict": 1024},
        )
        return response["message"]["content"]
    except Exception as e:
        logger.warning("Ollama call failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _call_backend(system_prompt: str, user_prompt: str, backend: str) -> Optional[str]:
    """Route to the appropriate backend."""
    if backend == "huggingface":
        return _call_huggingface(system_prompt, user_prompt)
    elif backend == "ollama":
        return _call_ollama(system_prompt, user_prompt)
    return None


def generate_llm_response(
    payload: Dict[str, Any],
    similar_cases: List[Tuple[Dict[str, Any], float]],
    backend: str,
) -> Optional[Dict[str, Any]]:
    """
    Generate narrative, next checks, and escalation summary via LLM.
    Returns parsed dict or None on any failure.
    """
    if backend == "placeholder":
        return None

    user_prompt = _format_investigation_context(payload, similar_cases)
    raw = _call_backend(_INVESTIGATION_SYSTEM_PROMPT, user_prompt, backend)
    if raw is None:
        return None
    return _extract_json(raw)


def assess_investigation_llm(
    payload: Dict[str, Any],
    similar_cases: List[Tuple[Dict[str, Any], float]],
    backend: str,
) -> Optional[Dict[str, str]]:
    """
    Use LLM to assess the investigation for the engineer.
    Returns dict with pattern, priority, confidence, diagnostic_approach, reasoning
    or None on failure.
    """
    if backend == "placeholder":
        return None

    user_prompt = _format_triage_context(payload, similar_cases)
    raw = _call_backend(_ASSESSMENT_SYSTEM_PROMPT, user_prompt, backend)
    if raw is None:
        return None
    return _extract_json(raw)
