import datetime as dt
from typing import Any, Dict, Optional

def build_payload(
    *,
    site: str,
    tool_group: str,
    process_step: str,
    severity: str,
    timestamp: dt.datetime,
    anomaly_summary: str,
    mode: str,
    form_metrics: Dict[str, Any],
    json_metrics: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Construct the request payload according to locked v1 input contract."""
    metrics: Dict[str, Any]
    if mode == "JSON":
        # Active mode wins
        metrics = dict(json_metrics or {})
    else:
        metrics = dict(form_metrics)

    return {
        "site": site,
        "tool_group": tool_group,
        "process_step": process_step,
        "severity": severity,
        "timestamp": timestamp.isoformat(),
        "anomaly_summary": anomaly_summary,
        "metrics": metrics,
        "metrics_input_mode": mode,
    }

