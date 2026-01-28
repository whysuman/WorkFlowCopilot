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

PERSIST_PATH = "requests_responses.jsonl"