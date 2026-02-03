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
                "matched_signals": "Limited data provided. The issue is described but key measurements are missing.",
                "resolution": "Start by narrowing the scope and verifying measurements. Escalate if the problem grows.",
            }
        ]
    else:
        # Provide up to 3 (but could be fewer)
        similar_cases = [
            {
                "similarity": "High" if severity == "high" else "Medium",
                "matched_signals": f"Quality change detected; rated as {severity} severity.",
                "resolution": "Verified measurement accuracy. Narrowed down by machine group. Reviewed recent changes.",
            },
            {
                "similarity": "Medium",
                "matched_signals": "Timing pattern matches — events clustered within the reported time window.",
                "resolution": "Identified affected batches. Isolated to specific manufacturing step. Prepared escalation package.",
            },
        ]
        if severity == "high":
            similar_cases.append(
                {
                    "similarity": "Medium",
                    "matched_signals": "High production impact. Could be a sudden event or a gradual shift.",
                    "resolution": "Cross-checked measurements. Compared recent configuration changes. Escalated with evidence.",
                }
            )

    next_checks: List[Dict[str, str]] = [
        {
            "category": "Narrow the scope",
            "check": "Break down the issue by location, machine, and process step. Compare affected vs unaffected areas to find what's different.",
            "why": "Confirm whether this is limited to one area or a wider systemic problem.",
        },
        {
            "category": "Verify the data",
            "check": "Double-check the measurements are accurate. Re-measure or use a different method to confirm the issue is real.",
            "why": "Avoid chasing a false alarm caused by bad measurements or data pipeline issues.",
        },
    ]

    if severity == "high":
        next_checks.append(
            {
                "category": "Check recent changes",
                "check": "Review any changes (process settings, software, maintenance) made within the reported time window.",
                "why": "High severity — prioritize finding if a recent change triggered this.",
            }
        )
        next_checks.append(
            {
                "category": "Prepare escalation",
                "check": "Package up: what happened, what's affected, what you've checked so far, and what's still unknown.",
                "why": "Enables fast handoff to specialists without losing investigation context.",
            }
        )
    else:
        next_checks.append(
            {
                "category": "Check recent changes",
                "check": "Look for any recent changes that line up with when the issue started.",
                "why": "Even moderate issues are often triggered by a change. Confirming this early narrows the search.",
            }
        )

    escalation_summary = (
        "Escalation summary (decision-support only):\n"
        f"- Observed: {payload.get('anomaly_summary', '').strip() or '[no summary provided]'}\n"
        f"- Context: facility={payload.get('site')}, machine group={payload.get('tool_group')}, "
        f"manufacturing step={payload.get('process_step')}, severity={payload.get('severity')}\n"
        f"- Evidence present: metrics_input_mode={payload.get('metrics_input_mode')}\n"
        "- Missing: scope analysis results and measurement cross-check notes\n"
        "- Recommendation: Proceed with the next checks. Escalate if the scope expands or data confidence is low.\n"
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
