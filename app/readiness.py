# app/readiness.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
import datetime as dt

from app.config import SITES, TOOL_GROUPS, PROCESS_STEPS, SEVERITY_LEVELS


def is_dropdown_filled(value: str, options: List[str]) -> bool:
    """Dropdown is 'filled' only if it is not the placeholder (index 0)."""
    return value is not None and len(options) > 0 and value != options[0]


def is_text_filled(value: str, min_chars: int = 1) -> bool:
    """Text is 'filled' if it meets the minimum non-whitespace length."""
    if value is None:
        return False
    return len(value.strip()) >= min_chars


def is_number_filled(value: Optional[float]) -> bool:
    """
    Numeric is 'filled' if it is not None.
    Note: if you later switch to default numeric values instead of None,
    you should change this logic (e.g., track 'touched' flags).
    """
    return value is not None


def compute_readiness(
    *,
    site: str,
    tool_group: str,
    process_step: str,
    severity: str,
    timestamp: dt.datetime,
    anomaly_summary: str,
    mode: str,
    form_metrics: Dict[str, Any],
    json_metrics_present: bool,
    anomaly_min_chars: int = 10,
) -> int:
    """
    Readiness % = (filled_fields / 13) * 100 with equal weighting.

    Groups:
      - Context (5): site, tool_group, process_step, severity, timestamp (counts as filled by default)
      - Core (4): anomaly_summary, yield_pct, affected_lot_count, time_window_hours
      - Advanced (4): metric_variance, change_magnitude, measurement_confidence, rework_rate

    Locked behavior:
      - JSON is NOT validated here (validate only on submit).
      - In JSON mode, metric fields are counted as filled if json_metrics_present is True.
    """
    filled = 0

    # -------------------------
    # Context (5)
    # -------------------------
    filled += int(is_dropdown_filled(site, SITES))
    filled += int(is_dropdown_filled(tool_group, TOOL_GROUPS))
    filled += int(is_dropdown_filled(process_step, PROCESS_STEPS))
    filled += int(is_dropdown_filled(severity, SEVERITY_LEVELS))
    filled += 1  # timestamp counts as filled by default

    # -------------------------
    # Core (4)
    # -------------------------
    filled += int(is_text_filled(anomaly_summary, min_chars=anomaly_min_chars))

    if mode == "Form":
        filled += int(is_number_filled(form_metrics.get("yield_pct")))
        filled += int(is_number_filled(form_metrics.get("affected_lot_count")))
        filled += int(is_number_filled(form_metrics.get("time_window_hours")))
    else:
        # JSON mode: treat all core metrics as "present" if textarea is non-empty
        filled += int(json_metrics_present)
        filled += int(json_metrics_present)
        filled += int(json_metrics_present)

    # -------------------------
    # Advanced (4)
    # -------------------------
    if mode == "Form":
        filled += int(is_number_filled(form_metrics.get("metric_variance")))
        filled += int(is_number_filled(form_metrics.get("change_magnitude")))
        filled += int(is_number_filled(form_metrics.get("measurement_confidence")))
        filled += int(is_number_filled(form_metrics.get("rework_rate")))
    else:
        # JSON mode: treat advanced metrics as "present" if textarea is non-empty
        filled += int(json_metrics_present)
        filled += int(json_metrics_present)
        filled += int(json_metrics_present)
        filled += int(json_metrics_present)

    pct = int((filled / 13) * 100)
    return max(0, min(100, pct))