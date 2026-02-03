"""
Investigation assessment (rule-based fallback when LLM is unavailable).

Engineer-facing: helps the engineer understand what type of problem
they're dealing with, how urgent it is, and how confident the system is
based on the available data.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Mapping from case family keywords to diagnostic pattern categories
FAMILY_PATTERN_MAP = {
    "unreliable measurements": "Measurement Problem",
    "single machine group": "Machine-Specific Issue",
    "gradual quality decline": "Gradual Drift",
    "configuration change": "Configuration Change Impact",
    "unexpected quality improvement": "False Alarm",
    "too many fixes": "Hidden Quality Issue",
    "inconsistent quality": "Batch-to-Batch Variation",
    "noisy data hiding": "Signal-to-Noise Problem",
    "sudden machine failure": "Critical Machine Failure",
    "slow wear": "Wear and Degradation",
}

# Suggested diagnostic approach per pattern
DIAGNOSTIC_APPROACH_MAP = {
    "Measurement Problem": "First check if the measurements themselves are reliable. Compare with a different measurement source before assuming the product is actually bad.",
    "Machine-Specific Issue": "Narrow it down to which specific machine is causing the issue. Compare output from the problem machine vs. working machines.",
    "Gradual Drift": "Look at the trend over the full time window. Check if something is slowly shifting rather than suddenly breaking.",
    "Configuration Change Impact": "Check what changed recently — process settings, software updates, or maintenance. Match the timing of the change to when quality dropped.",
    "False Alarm": "Verify the improvement is real, not a measurement error. If confirmed, update the quality thresholds to reflect the new baseline.",
    "Hidden Quality Issue": "Quality numbers look OK on the surface, but too many products need rework. Dig into the rework data to find the hidden problem.",
    "Batch-to-Batch Variation": "Compare batches to find what's different — raw materials, machine used, or process conditions. Look for a common factor in the bad batches.",
    "Signal-to-Noise Problem": "The data is too noisy to see the real signal. Filter the data more carefully or increase the sample size before drawing conclusions.",
    "Critical Machine Failure": "This machine likely needs to be taken offline immediately. Check maintenance logs and recent service history for clues.",
    "Wear and Degradation": "Look at the trend over the full time window. Check if any consumable parts are approaching their replacement schedule.",
    "Unknown": "Not enough data to identify a clear pattern. Start by narrowing the scope, then verify the measurements are reliable.",
}


def assess_investigation(
    payload: Dict[str, Any],
    similar_cases: Optional[List[Tuple[Dict[str, Any], float]]] = None,
) -> Dict[str, str]:
    """
    Rule-based investigation assessment for the engineer.

    Returns dict with:
      - pattern: the diagnostic pattern category
      - priority: Critical / High / Medium / Low
      - confidence: High / Medium / Low (based on data completeness)
      - diagnostic_approach: suggested first steps
      - reasoning: why this assessment was made
    """
    severity = payload.get("severity", "low")
    metrics = payload.get("metrics", {})
    yield_pct = metrics.get("yield_pct")
    change_mag = metrics.get("change_magnitude")
    rework = metrics.get("rework_rate")
    variance = metrics.get("metric_variance")

    # --- Pattern from top similar case ---
    pattern = "Unknown"
    if similar_cases:
        top_case, _score = similar_cases[0]
        family = top_case.get("family", "").lower()
        for keyword, pat in FAMILY_PATTERN_MAP.items():
            if keyword in family:
                pattern = pat
                break

    # --- Priority from severity + metrics ---
    if severity == "high":
        priority = "Critical" if (yield_pct is not None and yield_pct < 60) else "High"
    elif severity == "medium":
        priority = "High" if (yield_pct is not None and yield_pct < 80) else "Medium"
    else:
        priority = "Medium" if (change_mag is not None and abs(change_mag) > 10) else "Low"

    if yield_pct is not None and yield_pct < 30:
        priority = "Critical"
    if rework is not None and rework > 50 and priority not in ("Critical",):
        priority = "High"

    # --- Confidence based on data completeness ---
    filled_metrics = sum(1 for v in metrics.values() if v is not None)
    has_summary = bool(payload.get("anomaly_summary", "").strip())
    has_context = all(
        payload.get(k) and not str(payload.get(k, "")).startswith("—")
        for k in ("site", "tool_group", "process_step", "severity")
    )
    retrieval_quality = "none"
    if similar_cases:
        top_score = similar_cases[0][1]
        retrieval_quality = "high" if top_score >= 0.80 else ("medium" if top_score >= 0.60 else "low")

    confidence_score = 0
    confidence_score += min(filled_metrics, 7)  # 0-7 points
    confidence_score += 2 if has_summary else 0
    confidence_score += 2 if has_context else 0
    confidence_score += {"high": 3, "medium": 2, "low": 1, "none": 0}[retrieval_quality]

    if confidence_score >= 10:
        confidence = "High"
    elif confidence_score >= 6:
        confidence = "Medium"
    else:
        confidence = "Low"

    # --- Diagnostic approach ---
    diagnostic_approach = DIAGNOSTIC_APPROACH_MAP.get(pattern, DIAGNOSTIC_APPROACH_MAP["Unknown"])

    # --- Reasoning ---
    reason_parts = [f"severity={severity}"]
    if yield_pct is not None:
        reason_parts.append(f"quality rate={yield_pct:.1f}%")
    if pattern != "Unknown":
        reason_parts.append(f"pattern='{pattern}'")
    reason_parts.append(f"data confidence={confidence}")
    reasoning = f"Assessment based on: {', '.join(reason_parts)}."

    return {
        "pattern": pattern,
        "priority": priority,
        "confidence": confidence,
        "diagnostic_approach": diagnostic_approach,
        "reasoning": reasoning,
    }
