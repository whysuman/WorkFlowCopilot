import json
import os
import sys
import random
from datetime import datetime, timezone, timedelta

# --- 0. PATH SETUP & CONFIG LOADING ---
ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(ROOT, "app", "data", "realistic_cases.json")

sys.path.append(ROOT)

try:
    from app.config import SITES, TOOL_GROUPS, PROCESS_STEPS
except ImportError:
    print("❌ Error: Could not import config from app.config")
    sys.exit(1)

# --- 1. CONFIGURATION & GUARDS ---

assert SITES and SITES[0].startswith("—"), "SITES must start with a placeholder."
assert TOOL_GROUPS and TOOL_GROUPS[0].startswith("—"), "TOOL_GROUPS must start with a placeholder."
assert PROCESS_STEPS and PROCESS_STEPS[0].startswith("—"), "PROCESS_STEPS must start with a placeholder."

REAL_SITES = SITES[1:]
REAL_TOOL_GROUPS = TOOL_GROUPS[1:]
REAL_PROCESS_STEPS = PROCESS_STEPS[1:]

assert REAL_SITES and REAL_TOOL_GROUPS and REAL_PROCESS_STEPS, \
    "❌ Config lists must contain at least 1 real option after the placeholder."

METRIC_KEYS = {
    "yield_pct", "metric_variance", "change_magnitude", 
    "measurement_confidence", "affected_lot_count", 
    "rework_rate", "time_window_hours"
}

# --- 2. BUCKET DEFINITIONS ---

BUCKET_RANGES = {
    "yield_bucket": {
        "none": (91.5, 96.0),    # Normal Baseline
        "small": (89.0, 92.4),   # Mild dip
        "medium": (80.0, 88.9),  # Distinct drop
        "large": (50.0, 79.9)    # Catastrophic
    },
    "variance_bucket": {
        "low": (0.01, 0.15),
        "medium": (0.16, 0.35),
        "high": (0.36, 0.90)
    },
    "change_bucket": {
        "small": (0.1, 4.0),
        "medium": (4.1, 10.0),
        "large": (10.1, 25.0)
    },
    "measurement_bucket": {
        "low": (0.0, 0.50), "medium": (0.51, 0.80), "high": (0.81, 1.0)
    },
    "lots_bucket": {
        "small": (1, 3), "medium": (4, 10), "large": (11, 50)
    },
    "rework_bucket": {
        "low": (0.0, 2.0), "medium": (2.1, 8.0), "high": (8.1, 25.0)
    },
    "window_bucket": {
        "short": (1, 12), "medium": (13, 48), "long": (49, 168)
    }
}

# --- 3. PATTERN FAMILIES WITH CONSTRAINTS ---

# Filters for specific logic
def filter_tools(keyword):
    return [t for t in REAL_TOOL_GROUPS if keyword in t]

def filter_steps(keyword):
    return [s for s in REAL_PROCESS_STEPS if keyword in s]

FAMILIES = [
    {
        "title": "Yield dip coincident with metrology instability",
        "constraints": {
            "process_step": filter_steps("metrology") + filter_steps("inspection"),
            "tool_group": filter_tools("INSPECT") # Assuming INSPECT groups handle metrology
        },
        "signals": {
            "yield_bucket": "small", "variance_bucket": "high", "change_dir": "zero",
            "change_bucket": "small", "measurement_bucket": "low", "lots_bucket": "medium",
            "rework_bucket": "low", "window_bucket": "short"
        },
        "matched_template": "Matched: variance=high, measurement=low, window=short",
        "resolution": "Recalibrated measurement path; confirmed yield was stable after validation.",
        "hints": ["measurement_validation", "scope_segmentation"]
    },
    {
        "title": "Etch cluster excursion limited to one tool group",
        "constraints": {
            "process_step": filter_steps("etch"),
            "tool_group": filter_tools("ETCH")
        },
        "signals": {
            "yield_bucket": "medium", "variance_bucket": "medium", "change_dir": "neg",
            "change_bucket": "medium", "measurement_bucket": "high", "lots_bucket": "small",
            "rework_bucket": "medium", "window_bucket": "medium"
        },
        "matched_template": "Matched: context=tool_group, yield=medium, change=neg",
        "resolution": "Isolated to specific chamber; corrected config drift; monitored recovery.",
        "hints": ["scope_segmentation", "recent_changes_review"]
    },
    {
        "title": "Slow drift across sites over long window",
        "constraints": {}, # No constraints -> Systemic
        "signals": {
            "yield_bucket": "medium", "variance_bucket": "low", "change_dir": "neg",
            "change_bucket": "small", "measurement_bucket": "medium", "lots_bucket": "large",
            "rework_bucket": "medium", "window_bucket": "long"
        },
        "matched_template": "Matched: window=long, lots=large, drift-like change",
        "resolution": "Segmented by process_step; identified gradual parameter drift; escalated with evidence pack.",
        "hints": ["scope_segmentation", "escalation_packaging"]
    },
    {
        "title": "Yield shift after recent recipe change",
        "constraints": {}, # Can happen anywhere
        "signals": {
            "yield_bucket": "large", "variance_bucket": "medium", "change_dir": "neg",
            "change_bucket": "large", "measurement_bucket": "high", "lots_bucket": "medium",
            "rework_bucket": "high", "window_bucket": "short"
        },
        "matched_template": "Matched: window=short, change=neg large, rework=high",
        "resolution": "Rolled back change; validated with A/B lots; documented change correlation.",
        "hints": ["recent_changes_review", "escalation_packaging"]
    },
    {
        "title": "Positive yield shift causing false alarms",
        "constraints": {},
        "signals": {
            "yield_bucket": "none", "variance_bucket": "medium", "change_dir": "pos",
            "change_bucket": "large", "measurement_bucket": "medium", "lots_bucket": "medium",
            "rework_bucket": "low", "window_bucket": "short"
        },
        "matched_template": "Matched: change=pos, window=short",
        "resolution": "Validated new baseline; updated control limits to reflect improved performance.",
        "hints": ["recent_changes_review", "measurement_validation"]
    },
    {
        "title": "Yield stable but rework rate exceeding limits",
        "constraints": {
            "process_step": filter_steps("litho") + filter_steps("dep"),
            "tool_group": filter_tools("LITHO") + filter_tools("DEP")
        },
        "signals": {
            "yield_bucket": "small", "variance_bucket": "low", "change_dir": "zero",
            "change_bucket": "small", "measurement_bucket": "high", "lots_bucket": "large",
            "rework_bucket": "high", "window_bucket": "medium"
        },
        "matched_template": "Matched: rework=high, yield=small",
        "resolution": "Identified litho overlay alignment issue; forced recalibration.",
        "hints": ["scope_segmentation", "maintenance_logs_review"]
    },
    {
        "title": "Inconsistent yield across large lot population",
        "constraints": {},
        "signals": {
            "yield_bucket": "medium", "variance_bucket": "high", "change_dir": "neg",
            "change_bucket": "medium", "measurement_bucket": "medium", "lots_bucket": "large",
            "rework_bucket": "medium", "window_bucket": "medium"
        },
        "matched_template": "Matched: lots=large, variance=high",
        "resolution": "Correlated spread to raw material batch variance; quarantined specific batch.",
        "hints": ["scope_segmentation", "recent_changes_review"]
    },
    {
        "title": "High variance obscuring small yield degradation",
        "constraints": {},
        "signals": {
            "yield_bucket": "small", "variance_bucket": "high", "change_dir": "neg",
            "change_bucket": "small", "measurement_bucket": "medium", "lots_bucket": "medium",
            "rework_bucket": "low", "window_bucket": "medium"
        },
        "matched_template": "Matched: variance=high, yield=small, window=medium",
        "resolution": "Improved segmentation granularity; reduced noise with filters; confirmed mild degradation.",
        "hints": ["scope_segmentation", "measurement_validation"]
    },
    {
        "title": "Catastrophic yield drop on specific tool",
        "constraints": {
            # Could happen anywhere, but usually distinct to active processing
            "process_step": filter_steps("etch") + filter_steps("litho") + filter_steps("dep")
        },
        "signals": {
            "yield_bucket": "large", "variance_bucket": "low", "change_dir": "neg",
            "change_bucket": "large", "measurement_bucket": "high", "lots_bucket": "small",
            "rework_bucket": "low", "window_bucket": "short"
        },
        "matched_template": "Matched: yield=large drop, window=short",
        "resolution": "Emergency tool down; replaced failed RF generator; qualified tool recovery.",
        "hints": ["maintenance_logs_review", "escalation_packaging"]
    },
    {
        "title": "Gradual degradation approaching control limits",
        "constraints": {},
        "signals": {
            "yield_bucket": "medium", "variance_bucket": "medium", "change_dir": "neg",
            "change_bucket": "small", "measurement_bucket": "medium", "lots_bucket": "large",
            "rework_bucket": "low", "window_bucket": "long"
        },
        "matched_template": "Matched: window=long, change=small neg",
        "resolution": "Scheduled preventive maintenance (PM) pulled forward; replaced aging consumables.",
        "hints": ["scope_segmentation", "maintenance_logs_review"]
    }
]

# --- 4. GENERATION LOGIC ---

def generate_context(constraints):
    """
    Selects context based on family constraints.
    If constraint exists (e.g., only 'etch'), pick from that subset.
    Otherwise, pick from all REAL options.
    """
    # 1. Site: Usually random unless constrained (rare)
    site_pool = constraints.get("site", REAL_SITES)
    site = random.choice(site_pool) if site_pool else random.choice(REAL_SITES)

    # 2. Tool Group
    tool_pool = constraints.get("tool_group", REAL_TOOL_GROUPS)
    tool_group = random.choice(tool_pool) if tool_pool else random.choice(REAL_TOOL_GROUPS)

    # 3. Process Step
    step_pool = constraints.get("process_step", REAL_PROCESS_STEPS)
    process_step = random.choice(step_pool) if step_pool else random.choice(REAL_PROCESS_STEPS)

    return {
        "site": site,
        "tool_group": tool_group,
        "process_step": process_step
    }

def generate_metrics_with_physics(signals):
    """
    Generates metrics while respecting physical constraints.
    - Ensures Yield + Change doesn't exceed 100% or drop < 0%.
    - Handles the 'Positive Shift' vs 'High Yield' conflict.
    """
    metrics = {}
    
    # 1. Yield (The anchor)
    y_min, y_max = BUCKET_RANGES["yield_bucket"][signals["yield_bucket"]]
    yield_val = round(random.uniform(y_min, y_max), 2)
    metrics["yield_pct"] = yield_val
    
    # 2. Change Magnitude (The dependent variable)
    c_min, c_max = BUCKET_RANGES["change_bucket"][signals["change_bucket"]]
    
    # CLAMPING LOGIC (Option A)
    # If change is positive, we must ensure we don't imply >100% yield or look ridiculous
    # If yield is already 'none' (high ~93%), a 'large' pos change (+15) is impossible
    if signals["change_dir"] == "pos":
        # Calculate theoretical max room to grow
        max_room = 100.0 - yield_val
        # If the bucket range starts higher than max room, we have a physics conflict.
        # Force it to be smaller.
        if c_min > max_room:
            # Fallback: Generate a small realistic shift instead of the bucket's requested large one
            mag = random.uniform(0.1, max_room * 0.9)
        else:
            # Standard gen, but cap at max_room
            mag = random.uniform(c_min, min(c_max, max_room))
            
        mag = abs(mag) # Ensure positive

    elif signals["change_dir"] == "neg":
        # If change is negative, we can't have dropped more than the yield existed (mostly safe for % yield)
        # But generally safe unless yield is very low
        mag = random.uniform(c_min, c_max)
        mag = -abs(mag) # Ensure negative
    else:
        mag = 0.0

    metrics["change_magnitude"] = round(mag, 2)
    
    # 3. Variance
    v_min, v_max = BUCKET_RANGES["variance_bucket"][signals["variance_bucket"]]
    metrics["metric_variance"] = round(random.uniform(v_min, v_max), 3)
    
    # 4. Confidence
    m_min, m_max = BUCKET_RANGES["measurement_bucket"][signals["measurement_bucket"]]
    metrics["measurement_confidence"] = round(random.uniform(m_min, m_max), 2)
    
    # 5. Lots
    l_min, l_max = BUCKET_RANGES["lots_bucket"][signals["lots_bucket"]]
    metrics["affected_lot_count"] = random.randint(l_min, l_max)
    
    # 6. Rework
    r_min, r_max = BUCKET_RANGES["rework_bucket"][signals["rework_bucket"]]
    metrics["rework_rate"] = round(random.uniform(r_min, r_max), 2)
    
    # 7. Time Window
    w_min, w_max = BUCKET_RANGES["window_bucket"][signals["window_bucket"]]
    metrics["time_window_hours"] = random.randint(w_min, w_max)
    
    return metrics

def generate_timestamp():
    """Returns an ISO timestamp randomly distributed over the last 180 days."""
    days_ago = random.randint(0, 180)
    # Add random seconds to avoid exact same time
    seconds_offset = random.randint(0, 86400)
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago, seconds=seconds_offset)
    return dt.isoformat()

# --- 5. EXECUTION ---

def generate():
    cases = []
    case_counter = 1
    random.seed(42)
    
    for family in FAMILIES:
        for _ in range(5):
            case_id = f"C-{case_counter:03d}"
            
            # 1. Generate Context (Weighted/Constrained)
            context = generate_context(family.get("constraints", {}))
            
            # 2. Generate Metrics (Physics-Aware)
            metrics = generate_metrics_with_physics(family["signals"])
            
            # Sanity Check
            assert set(metrics.keys()) == METRIC_KEYS, f"Schema mismatch in {case_id}"
            
            case_record = {
                "case_id": case_id,
                "created_at": generate_timestamp(),
                "family": family["title"],
                "title": family["title"],
                "context": context,
                "metrics": metrics,
                "signals": family["signals"],
                "matched_signals_template": family["matched_template"],
                "resolution_summary": family["resolution"],
                "next_checks_hint": family["hints"]
            }
            cases.append(case_record)
            case_counter += 1
            
    return cases

if __name__ == "__main__":
    print(f"Generating synthetic cases...")
    data = generate()
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Successfully wrote {len(data)} high-fidelity cases to:\n   {OUTPUT_PATH}")