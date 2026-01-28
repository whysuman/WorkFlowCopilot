from typing import Dict, Any, List
import datetime as dt


def build_placeholder_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder v1 response (Milestone 1):
      - similar_cases: 0-3
      - next_checks: min 2
      - escalation_summary: always visible
      - narrative: placeholder
    """
    severity = payload.get("severity", "low")
    metrics = payload.get("metrics", {})
    yield_pct = metrics.get("yield_pct")

    # Use simple heuristic just to make placeholders feel alive (not "smart").
    similar_cases: List[Dict[str, str]] = []
    no_strong_match_note = None

    if yield_pct is None:
        # If missing key metrics, show weaker match situation.
        no_strong_match_note = "No strong matches found — showing best available references."
        similar_cases = [
            {
                "similarity": "Low",
                "matched_signals": "Sparse metrics; anomaly described but core signals missing.",
                "resolution": "Start with segmentation + measurement validation; escalate if scope expands.",
            }
        ]
    else:
        # Provide up to 3 (but could be fewer)
        similar_cases = [
            {
                "similarity": "High" if severity == "high" else "Medium",
                "matched_signals": f"Yield shift observed; severity='{severity}'.",
                "resolution": "Validated measurement path; segmented by tool_group; reviewed recent changes.",
            },
            {
                "similarity": "Medium",
                "matched_signals": "Temporal clustering within the provided time window.",
                "resolution": "Scoped impacted lots; isolated to process_step segment; documented escalation pack.",
            },
        ]
        if severity == "high":
            similar_cases.append(
                {
                    "similarity": "Medium",
                    "matched_signals": "High operational impact signal; potential drift vs shift ambiguity.",
                    "resolution": "Ran measurement cross-check; compared recent recipe/config changes; escalated with evidence.",
                }
            )

    next_checks: List[Dict[str, str]] = [
        {
            "category": "Scope & segmentation",
            "check": "Segment the anomaly by site/tool_group/process_step and compare impacted vs non-impacted slices.",
            "why": "Confirm whether this is localized (single segment) or systemic (multi-segment).",
        },
        {
            "category": "Measurement validation",
            "check": "Validate measurement confidence: repeat measurement or cross-check with an independent signal.",
            "why": "Avoid chasing a false anomaly caused by instrumentation or data pipeline issues.",
        },
    ]

    if severity == "high":
        next_checks.append(
            {
                "category": "Recent changes review",
                "check": "Review recent changes (recipes/configs/maintenance/software) within the reported time window.",
                "why": "High severity warrants prioritizing change-driven hypotheses early.",
            }
        )
        next_checks.append(
            {
                "category": "Escalation packaging",
                "check": "Prepare an escalation packet: summary, scope, evidence, missing info, and next steps attempted.",
                "why": "Enables fast handoff to SMEs without losing investigation context.",
            }
        )
    else:
        next_checks.append(
            {
                "category": "Recent changes review",
                "check": "Check for any recent changes that align with the anomaly start time.",
                "why": "Even moderate issues are often change-correlated; confirm early to reduce search space.",
            }
        )

    escalation_summary = (
        "Escalation summary (decision-support only):\n"
        f"- Observed: {payload.get('anomaly_summary', '').strip() or '[no summary provided]'}\n"
        f"- Context: site={payload.get('site')}, tool_group={payload.get('tool_group')}, "
        f"process_step={payload.get('process_step')}, severity={payload.get('severity')}\n"
        f"- Evidence present: metrics_input_mode={payload.get('metrics_input_mode')}\n"
        "- Missing: additional segmentation results and measurement cross-check notes\n"
        "- Recommendation: Proceed with the next checks; escalate if scope expands or confidence is low.\n"
    )

    narrative = (
        "AI narrative (placeholder): This section will later provide constrained synthesis only—"
        "no root-cause claims, no invented checks."
    )

    resp = {
        "similar_cases": similar_cases[:3],
        "no_strong_match_note": no_strong_match_note,
        "next_checks": next_checks,
        "escalation_summary": escalation_summary,
        "narrative": narrative,
        "meta": {
            "response_id": f"resp_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        },
    }
    return resp

