SITES = [
    "— Select site —",
    "Plant-A",
    "Plant-B",
    "Plant-C",
    "Plant-D",
]

TOOL_GROUPS = [
    "— Select tool group —",
    "ETCH-CLUSTER-1",
    "ETCH-CLUSTER-2",
    "LITHO-LINE-1",
    "LITHO-LINE-2",
    "DEP-STACK-1",
    "INSPECT-GROUP-1",
]

PROCESS_STEPS = [
    "— Select process step —",
    "lithography",
    "etch",
    "deposition",
    "inspection",
    "metrology",
]

SEVERITY_LEVELS = [
    "— Select severity —",
    "low",
    "medium",
    "high",
]

DEFAULTS = {
    "yield_pct": 92.5,
    "affected_lot_count": 6,
    "time_window_hours": 48,
    "metric_variance": 0.12,
    "change_magnitude": -4.8,
    "measurement_confidence": 0.78,
    "rework_rate": 4.2,
}

BUCKET_RANGES = {
    "yield_severity": {
        # Lower is worse. 
        "large":  (0.0, 80.0),    # < 80%
        "medium": (80.0, 89.0),   # 80.0 up to 88.99...
        "small":  (89.0, 92.5),   # 89.0 up to 92.49...
        "none":   (92.5, 100.1)   # Baseline (Includes 100.0)
    },
    "variance_bucket": {
        "low":    (0.0, 0.16),
        "medium": (0.16, 0.36),
        "high":   (0.36, 1.01)    # >0.9 indicates severe instability
    },
    "change_bucket": {
        "small":  (0.0, 4.1),
        "medium": (4.1, 10.1),
        "large":  (10.1, 100.0)
    },
    "measurement_bucket": {
        "low":    (0.0, 0.51),
        "medium": (0.51, 0.81),
        "high":   (0.81, 1.01)
    },
    "lots_bucket": {
        # Integers. Logic: 1, 2, 3 -> small. 4..10 -> medium.
        "small":  (1, 4),         # Starts at 1. 0 is invalid.
        "medium": (4, 11),
        "large":  (11, 1000)
    },
    "rework_bucket": {
        "low":    (0.0, 2.1),
        "medium": (2.1, 8.1),
        "high":   (8.1, 100.0)
    },
    "window_bucket": {
        # Hours. Starts at 1. 0 is invalid.
        "short":  (1, 13),        # 1 to 12 hours
        "medium": (13, 49),       # 13 to 48 hours
        "long":   (49, 1000)      # 49+ hours
    }
}

import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PERSIST_PATH = os.path.join(_PROJECT_ROOT, "output", "requests_responses.jsonl")
CASES_PATH = os.path.join(_PROJECT_ROOT, "data", "realistic_cases.json")
CHROMA_PERSIST_DIR = os.path.join(_PROJECT_ROOT, "data", "chroma_db")