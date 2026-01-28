from app.schema import METRIC_KEYS
import json
from typing import Any, Dict, Optional, Tuple

def validate_metrics_json(raw: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Strict validation (locked):
      - valid JSON object (dict)
      - keys must match METRIC_KEYS exactly (no missing, no extras)
      - strict numeric types for values (int/float only; reject strings)
    Returns: (metrics_dict or None, error_message or None)
    """
    if raw is None or raw.strip() == "":
        return None, "Metrics JSON is empty."

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e.msg} (pos {e.pos})"

    if not isinstance(parsed, dict):
        return None, "Metrics JSON must be an object/dictionary."

    keys = set(parsed.keys())
    missing = METRIC_KEYS - keys
    extra = keys - METRIC_KEYS
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"Missing keys: {sorted(missing)}")
        if extra:
            parts.append(f"Extra keys: {sorted(extra)}")
        return None, "Schema mismatch. " + " | ".join(parts)

    # Strict numeric types
    for k, v in parsed.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None, f"Key '{k}' must be a number (int/float), got {type(v).__name__}."

    return parsed, None

