import json
import os
import sys
import random
import numpy as np
from datetime import datetime, timezone, timedelta
from scipy import stats
from scipy.stats import beta, lognorm, poisson

# --- 0. PATH SETUP & CONFIG LOADING ---
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(ROOT, "data", "realistic_cases.json")

sys.path.append(ROOT)

try:
    from app.config import SITES, TOOL_GROUPS, PROCESS_STEPS, BUCKET_RANGES
    from app.core.schema import METRIC_KEYS
except ImportError:
    print(" Error: Could not import config from app.config")
    sys.exit(1)

# --- 1. CONFIGURATION & GUARDS ---

assert SITES and SITES[0].startswith("—"), "SITES must start with a placeholder."
assert TOOL_GROUPS and TOOL_GROUPS[0].startswith("—"), "TOOL_GROUPS must start with a placeholder."
assert PROCESS_STEPS and PROCESS_STEPS[0].startswith("—"), "PROCESS_STEPS must start with a placeholder."

REAL_SITES = SITES[1:]
REAL_TOOL_GROUPS = TOOL_GROUPS[1:]
REAL_PROCESS_STEPS = PROCESS_STEPS[1:]

assert REAL_SITES and REAL_TOOL_GROUPS and REAL_PROCESS_STEPS, \
    " Config lists must contain at least 1 real option."



# --- 2. REALISTIC DISTRIBUTION HELPERS ---

def sample_from_beta_in_range(lo, hi, alpha=2.0, beta_param=5.0, clamp_hi=None):
    """
    Sample from beta distribution mapped to [lo, hi) range.
    Beta distribution creates more realistic clustering patterns.

    Default params (alpha=2, beta=5) create right-skewed distribution
    suitable for yields (most values high, some low).
    """
    sample = np.random.beta(alpha, beta_param)

    # Map to range
    val = lo + sample * (hi - lo)

    # Physical clamp
    if clamp_hi is not None:
        val = min(val, clamp_hi)

    # Ensure within [lo, hi)
    epsilon = 1e-6
    val = max(lo, min(val, hi - epsilon))

    rounded = round(val, 2)
    if rounded >= hi:
        rounded = round(hi - 0.01, 2)
    if rounded < lo:
        rounded = lo
    return rounded


def sample_from_lognormal_in_range(lo, hi, sigma=0.5):
    """
    Sample from log-normal distribution for metrics like variance.
    Common in semiconductor data due to multiplicative processes.
    """
    mid = (lo + hi) / 2
    mu = np.log(mid)

    sample = np.random.lognormal(mu, sigma)

    # Clamp to [lo, hi)
    epsilon = 1e-6
    val = max(lo, min(sample, hi - epsilon))

    rounded = round(val, 3)
    if rounded >= hi:
        rounded = round(hi - 0.001, 3)
    if rounded < lo:
        rounded = lo
    return rounded


def sample_poisson_in_range(lo, hi, lambda_param=None):
    """
    Sample from Poisson distribution for count data (lots).
    If lambda not provided, use midpoint of range.
    """
    if lambda_param is None:
        lambda_param = (lo + hi) / 2

    sample = np.random.poisson(lambda_param)

    # Clamp to [lo, hi)
    val = max(int(lo), min(sample, int(hi) - 1))

    return max(1, val)  # Ensure at least 1


def sample_truncated_normal_in_range(lo, hi, mean=None, std=None, clamp_hi=None):
    """
    Sample from truncated normal distribution.
    Good for metrics with central tendency like measurement confidence.
    """
    if mean is None:
        mean = (lo + hi) / 2
    if std is None:
        std = (hi - lo) / 6  # 3-sigma covers range

    a = (lo - mean) / std
    b = (hi - mean) / std
    sample = stats.truncnorm.rvs(a, b, loc=mean, scale=std)

    # Physical clamp
    if clamp_hi is not None:
        sample = min(sample, clamp_hi)

    epsilon = 1e-6
    val = max(lo, min(sample, hi - epsilon))

    rounded = round(val, 2)
    if rounded >= hi:
        rounded = round(hi - 0.01, 2)
    if rounded < lo:
        rounded = lo
    return rounded


# --- 3. CORRELATION MATRIX ---

def apply_correlations(base_metrics, signals):
    """
    Apply realistic correlations between metrics based on semiconductor physics.

    Correlations observed in real manufacturing:
    - High variance → Lower measurement confidence
    - Large yield drops → Higher rework rates
    - Long time windows → More affected lots
    - High variance → Higher rework rate

    FIX APPLIED: After each adjustment, the value is re-clamped to its
    target bucket range. Without this, correlations can push values across
    bucket boundaries, causing downstream validation failures.
    """
    metrics = base_metrics.copy()

    # Correlation 1: High variance reduces measurement confidence
    if signals["variance_bucket"] == "high":
        current_conf = metrics["measurement_confidence"]
        noise_factor = np.random.uniform(0.85, 0.95)
        adjusted = round(max(0.1, current_conf * noise_factor), 2)

        # Re-clamp to target measurement bucket
        m_min, m_max = BUCKET_RANGES["measurement_bucket"][signals["measurement_bucket"]]
        metrics["measurement_confidence"] = max(m_min, min(adjusted, round(m_max - 0.01, 2)))

    # Correlation 2: Large negative yield change increases rework
    if signals["change_dir"] == "neg" and abs(metrics["change_magnitude"]) > 5.0:
        current_rework = metrics["rework_rate"]
        boost_factor = 1.0 + abs(metrics["change_magnitude"]) * 0.05
        adjusted = round(current_rework * boost_factor, 2)

        # Re-clamp to target rework bucket
        r_min, r_max = BUCKET_RANGES["rework_bucket"][signals["rework_bucket"]]
        metrics["rework_rate"] = max(r_min, min(adjusted, round(r_max - 0.01, 2)))

    # Correlation 3: Long time windows correlate with more lots
    if signals["window_bucket"] == "long":
        current_lots = metrics["affected_lot_count"]
        boost = np.random.randint(5, 15)
        adjusted = current_lots + boost

        # Re-clamp to target lots bucket
        l_min, l_max = BUCKET_RANGES["lots_bucket"][signals["lots_bucket"]]
        metrics["affected_lot_count"] = max(l_min, min(adjusted, l_max - 1))

    # Correlation 4: Variance and rework correlation
    if signals["variance_bucket"] in ["medium", "high"]:
        variance_val = metrics["metric_variance"]
        current_rework = metrics["rework_rate"]
        variance_penalty = variance_val * 10  # variance is 0-1
        adjusted = round(current_rework + variance_penalty, 2)

        # Re-clamp to target rework bucket
        r_min, r_max = BUCKET_RANGES["rework_bucket"][signals["rework_bucket"]]
        metrics["rework_rate"] = max(r_min, min(adjusted, round(r_max - 0.01, 2)))

    return metrics


# --- 4. IMPROVED METRIC GENERATION ---

def generate_metrics_realistic(signals, family_title):
    """
    Generate metrics using realistic statistical distributions.
    Uses Beta, Log-normal, Poisson, and Truncated Normal distributions
    based on semiconductor manufacturing literature.

    FIX APPLIED (STEP 4): safe_c_max is rounded to 2 decimal places before
    being passed to the sampling functions. This snaps floating-point drift
    (e.g., 100.0 - 95.9 = 4.0999...94 instead of 4.1) back to the clean
    bucket boundary, preventing the sampler from producing values that
    round onto the exclusive upper bound and fail bucket classification.
    """
    metrics = {}

    # --- STEP 1: Resolve change constraints ---
    c_min, c_max = BUCKET_RANGES["change_bucket"][signals["change_bucket"]]
    change_dir = signals["change_dir"]

    # --- STEP 2: Feasible yield range ---
    y_min, y_max = BUCKET_RANGES["yield_severity"][signals["yield_severity"]]
    feasible_y_lo, feasible_y_hi = y_min, y_max

    if change_dir == "neg":
        eps = 1e-6
        max_phys_yield = 100.0 - c_min - eps
        feasible_y_hi = min(feasible_y_hi, max_phys_yield)
    elif change_dir == "pos":
        feasible_y_lo = max(feasible_y_lo, c_min)

    if feasible_y_lo >= feasible_y_hi:
        raise ValueError(
            f" IMPOSSIBLE DEFINITION in '{family_title}':\n"
            f"   Yield bucket '{signals['yield_severity']}' ({y_min}-{y_max}) has no feasible overlap with\n"
            f"   Change bucket '{signals['change_bucket']}' (dir={change_dir}, {c_min}-{c_max}).\n"
            f"   Resulting yield range is empty: [{feasible_y_lo}, {feasible_y_hi}]"
        )

    # --- STEP 3: Generate yield using Beta distribution ---
    if signals["yield_severity"] in ["large", "medium"]:
        yield_val = sample_from_beta_in_range(
            feasible_y_lo, feasible_y_hi, alpha=2.5, beta_param=3.0, clamp_hi=100.0
        )
    else:
        yield_val = sample_from_beta_in_range(
            feasible_y_lo, feasible_y_hi, alpha=3.0, beta_param=2.0, clamp_hi=100.0
        )
    metrics["yield_pct"] = yield_val

    # --- STEP 4: Generate change with realistic distribution ---
    # FIX: round safe_c_max to 2 decimals to snap float drift back to the
    # clean bucket boundary before passing to the sampler.
    if change_dir == "neg":
        phys_c_max = 100.0 - yield_val
        actual_c_max = min(c_max, phys_c_max)
        safe_c_max = round(max(actual_c_max, c_min), 2)  # ← FIX: snap float drift

        mag = sample_from_lognormal_in_range(c_min, safe_c_max, sigma=0.4)
        metrics["change_magnitude"] = -mag

    elif change_dir == "pos":
        phys_c_max = yield_val
        actual_c_max = min(c_max, phys_c_max)
        safe_c_max = round(max(actual_c_max, c_min), 2)  # ← FIX: snap float drift

        mag = sample_from_beta_in_range(c_min, safe_c_max, alpha=2.0, beta_param=4.0)
        metrics["change_magnitude"] = mag
    else:
        metrics["change_magnitude"] = 0.0

    # --- STEP 5: Variance using log-normal (multiplicative errors) ---
    v_min, v_max = BUCKET_RANGES["variance_bucket"][signals["variance_bucket"]]

    if signals["variance_bucket"] == "high":
        metrics["metric_variance"] = sample_from_lognormal_in_range(
            v_min, v_max, sigma=0.6
        )
    else:
        metrics["metric_variance"] = sample_from_lognormal_in_range(
            v_min, v_max, sigma=0.3
        )
    metrics["metric_variance"] = min(1.0, metrics["metric_variance"])

    # --- STEP 6: Measurement confidence (truncated normal) ---
    m_min, m_max = BUCKET_RANGES["measurement_bucket"][signals["measurement_bucket"]]

    if signals["measurement_bucket"] == "high":
        mean = m_min + 0.75 * (m_max - m_min)
    elif signals["measurement_bucket"] == "low":
        mean = m_min + 0.25 * (m_max - m_min)
    else:
        mean = (m_min + m_max) / 2

    metrics["measurement_confidence"] = sample_truncated_normal_in_range(
        m_min, m_max, mean=mean, clamp_hi=1.0
    )

    # --- STEP 7: Lot count (Poisson distribution) ---
    l_min, l_max = BUCKET_RANGES["lots_bucket"][signals["lots_bucket"]]
    l_min = max(1, l_min)

    if signals["lots_bucket"] == "large":
        lambda_lots = (l_min + l_max) * 0.6
    elif signals["lots_bucket"] == "small":
        lambda_lots = (l_min + l_max) * 0.3
    else:
        lambda_lots = (l_min + l_max) * 0.5

    metrics["affected_lot_count"] = sample_poisson_in_range(l_min, l_max, lambda_lots)

    # --- STEP 8: Rework rate (beta distribution) ---
    r_min, r_max = BUCKET_RANGES["rework_bucket"][signals["rework_bucket"]]

    if signals["rework_bucket"] == "high":
        metrics["rework_rate"] = sample_from_beta_in_range(
            r_min, r_max, alpha=4.0, beta_param=2.0, clamp_hi=100.0
        )
    else:
        metrics["rework_rate"] = sample_from_beta_in_range(
            r_min, r_max, alpha=2.0, beta_param=5.0, clamp_hi=100.0
        )

    # --- STEP 9: Time window (Poisson for count-like data) ---
    w_min, w_max = BUCKET_RANGES["window_bucket"][signals["window_bucket"]]
    w_min = max(1, w_min)

    if signals["window_bucket"] == "long":
        lambda_window = (w_min + w_max) * 0.6
    elif signals["window_bucket"] == "short":
        lambda_window = (w_min + w_max) * 0.3
    else:
        lambda_window = (w_min + w_max) * 0.5

    metrics["time_window_hours"] = sample_poisson_in_range(w_min, w_max, lambda_window)

    # --- STEP 10: Apply correlations ---
    metrics = apply_correlations(metrics, signals)

    # Schema sanity check
    assert set(metrics.keys()) == METRIC_KEYS, f"Schema mismatch: got {set(metrics.keys())}"

    return metrics


def classify_value(value, category):
    """
    Classifies a value into a bucket using strict [lo, hi) logic.
    """
    ranges = BUCKET_RANGES[category]

    if category == "change_bucket":
        value = abs(value)

    for label, (lo, hi) in sorted(ranges.items(), key=lambda kv: kv[1][0]):
        if lo <= value < hi:
            return label
    return "unknown"


def validate_case(case, signals):
    """
    Post-generation validation. Asserts every generated value lands
    in its target bucket and that sign semantics are correct.
    """
    m = case["metrics"]

    checks = [
        ("yield_pct",                "yield_severity"),
        ("metric_variance",          "variance_bucket"),
        ("measurement_confidence",   "measurement_bucket"),
        ("affected_lot_count",       "lots_bucket"),
        ("rework_rate",              "rework_bucket"),
        ("time_window_hours",        "window_bucket"),
    ]

    for key, bucket_name in checks:
        actual_label = classify_value(m[key], bucket_name)
        expected_label = signals[bucket_name]
        assert actual_label == expected_label, (
            f" Validation Mismatch [{key}]: {m[key]} classified as '{actual_label}', "
            f"expected '{expected_label}'"
        )

    # Change bucket check (uses abs internally)
    if signals["change_dir"] != "zero":
        actual_label = classify_value(m["change_magnitude"], "change_bucket")
        expected_label = signals["change_bucket"]
        assert actual_label == expected_label, (
            f" Validation Mismatch [change_magnitude]: {m['change_magnitude']} classified as "
            f"'{actual_label}', expected '{expected_label}'"
        )

    # Sign semantics
    if signals["change_dir"] == "neg":
        assert m["change_magnitude"] <= -1e-9, (
            f" Sign Mismatch: Expected negative change, got {m['change_magnitude']}"
        )
    elif signals["change_dir"] == "pos":
        assert m["change_magnitude"] >= 1e-9, (
            f" Sign Mismatch: Expected positive change, got {m['change_magnitude']}"
        )
    else:
        assert abs(m["change_magnitude"]) < 1e-9, (
            f" Sign Mismatch: Expected zero change, got {m['change_magnitude']}"
        )


# --- 5. PATTERN FAMILIES ---

def filter_tools(keyword):
    return [t for t in REAL_TOOL_GROUPS if keyword.lower() in t.lower()]

def filter_steps(keyword):
    return [s for s in REAL_PROCESS_STEPS if keyword.lower() in s.lower()]

FAMILIES = [
    {
        "title": "Quality drop caused by unreliable measurements",
        "constraints": {
            "process_step": filter_steps("metrology") + filter_steps("inspection"),
            "tool_group": filter_tools("INSPECT"),
        },
        "signals": {
            "yield_severity": "small",
            "variance_bucket": "high",
            "change_dir": "zero",
            "change_bucket": "small",
            "measurement_bucket": "low",
            "lots_bucket": "medium",
            "rework_bucket": "low",
            "window_bucket": "short",
        },
        "matched_template": "Pattern: unstable measurements + low data confidence + recent onset",
        "resolution": "Recalibrated the measurement equipment. Confirmed quality was actually stable — the measurements were the problem, not the product.",
        "hints": ["verify_measurements", "narrow_scope"],
    },
    {
        "title": "Single machine group producing defects",
        "constraints": {
            "process_step": filter_steps("etch"),
            "tool_group": filter_tools("ETCH"),
        },
        "signals": {
            "yield_severity": "medium",
            "variance_bucket": "medium",
            "change_dir": "neg",
            "change_bucket": "medium",
            "measurement_bucket": "high",
            "lots_bucket": "small",
            "rework_bucket": "medium",
            "window_bucket": "medium",
        },
        "matched_template": "Pattern: issue limited to one machine group + moderate quality decline",
        "resolution": "Narrowed the problem to one specific machine chamber. Fixed a configuration that had drifted from spec. Monitored until quality recovered.",
        "hints": ["narrow_scope", "check_recent_changes"],
    },
    {
        "title": "Gradual quality decline across multiple facilities",
        "constraints": {},
        "signals": {
            "yield_severity": "medium",
            "variance_bucket": "low",
            "change_dir": "neg",
            "change_bucket": "small",
            "measurement_bucket": "medium",
            "lots_bucket": "large",
            "rework_bucket": "medium",
            "window_bucket": "long",
        },
        "matched_template": "Pattern: long time window + many batches affected + slow decline",
        "resolution": "Broke down the data by manufacturing step and found a gradual parameter drift. Packaged the evidence and escalated to the engineering team.",
        "hints": ["narrow_scope", "prepare_escalation"],
    },
    {
        "title": "Quality drop after process configuration change",
        "constraints": {},
        "signals": {
            "yield_severity": "large",
            "variance_bucket": "medium",
            "change_dir": "neg",
            "change_bucket": "large",
            "measurement_bucket": "high",
            "lots_bucket": "medium",
            "rework_bucket": "high",
            "window_bucket": "short",
        },
        "matched_template": "Pattern: sudden onset + large quality drop + high rework rate",
        "resolution": "Rolled back the configuration change. Ran comparison tests between old and new settings to confirm the change caused the problem. Documented the correlation.",
        "hints": ["check_recent_changes", "prepare_escalation"],
    },
    {
        "title": "Unexpected quality improvement (false alarm)",
        "constraints": {},
        "signals": {
            "yield_severity": "none",
            "variance_bucket": "medium",
            "change_dir": "pos",
            "change_bucket": "large",
            "measurement_bucket": "medium",
            "lots_bucket": "medium",
            "rework_bucket": "low",
            "window_bucket": "short",
        },
        "matched_template": "Pattern: positive shift + sudden onset + no quality issues",
        "resolution": "Confirmed the improvement was real, not a measurement error. Updated the quality thresholds to reflect the new, better baseline.",
        "hints": ["check_recent_changes", "verify_measurements"],
    },
    {
        "title": "Products pass but need too many fixes",
        "constraints": {
            "process_step": filter_steps("litho") + filter_steps("dep"),
            "tool_group": filter_tools("LITHO") + filter_tools("DEP"),
        },
        "signals": {
            "yield_severity": "small",
            "variance_bucket": "low",
            "change_dir": "zero",
            "change_bucket": "small",
            "measurement_bucket": "high",
            "lots_bucket": "large",
            "rework_bucket": "high",
            "window_bucket": "medium",
        },
        "matched_template": "Pattern: quality looks OK but rework rate is too high",
        "resolution": "Found a machine alignment issue that was causing products to need extra fixing. Forced a recalibration of the affected machine.",
        "hints": ["narrow_scope", "check_maintenance_logs"],
    },
    {
        "title": "Inconsistent quality across many production batches",
        "constraints": {},
        "signals": {
            "yield_severity": "medium",
            "variance_bucket": "high",
            "change_dir": "neg",
            "change_bucket": "medium",
            "measurement_bucket": "medium",
            "lots_bucket": "large",
            "rework_bucket": "medium",
            "window_bucket": "medium",
        },
        "matched_template": "Pattern: many batches affected + high variability between batches",
        "resolution": "Traced the inconsistency to a bad batch of raw materials. Quarantined the affected material and quality stabilized.",
        "hints": ["narrow_scope", "check_recent_changes"],
    },
    {
        "title": "Noisy data hiding a real quality decline",
        "constraints": {},
        "signals": {
            "yield_severity": "small",
            "variance_bucket": "high",
            "change_dir": "neg",
            "change_bucket": "small",
            "measurement_bucket": "medium",
            "lots_bucket": "medium",
            "rework_bucket": "low",
            "window_bucket": "medium",
        },
        "matched_template": "Pattern: high measurement noise + small but real quality drop",
        "resolution": "Filtered out the noise by analyzing more granular data. Confirmed a mild but real quality degradation that was being masked by noisy measurements.",
        "hints": ["narrow_scope", "verify_measurements"],
    },
    {
        "title": "Sudden machine failure causing massive quality drop",
        "constraints": {
            "process_step": filter_steps("etch") + filter_steps("litho") + filter_steps("dep"),
        },
        "signals": {
            "yield_severity": "large",
            "variance_bucket": "low",
            "change_dir": "neg",
            "change_bucket": "large",
            "measurement_bucket": "high",
            "lots_bucket": "small",
            "rework_bucket": "low",
            "window_bucket": "short",
        },
        "matched_template": "Pattern: sudden large quality drop + few batches + very recent",
        "resolution": "Emergency shutdown of the machine. Replaced a failed hardware component. Ran qualification tests to confirm the machine was working again.",
        "hints": ["check_maintenance_logs", "prepare_escalation"],
    },
    {
        "title": "Slow wear approaching maintenance threshold",
        "constraints": {},
        "signals": {
            "yield_severity": "medium",
            "variance_bucket": "medium",
            "change_dir": "neg",
            "change_bucket": "small",
            "measurement_bucket": "medium",
            "lots_bucket": "large",
            "rework_bucket": "low",
            "window_bucket": "long",
        },
        "matched_template": "Pattern: long time window + small gradual decline + many batches",
        "resolution": "Pulled forward a scheduled maintenance. Replaced aging consumable parts that were slowly wearing out. Quality returned to normal.",
        "hints": ["narrow_scope", "check_maintenance_logs"],
    },
]

# --- 6. EXECUTION ---

def generate_context(constraints):
    site_pool = constraints.get("site", REAL_SITES)
    site = random.choice(site_pool) if site_pool else random.choice(REAL_SITES)

    tool_pool = constraints.get("tool_group", REAL_TOOL_GROUPS)
    tool_group = random.choice(tool_pool) if tool_pool else random.choice(REAL_TOOL_GROUPS)

    step_pool = constraints.get("process_step", REAL_PROCESS_STEPS)
    process_step = random.choice(step_pool) if step_pool else random.choice(REAL_PROCESS_STEPS)

    return {"site": site, "tool_group": tool_group, "process_step": process_step}


def generate_timestamp_realistic():
    """
    Generate timestamps with realistic clustering patterns.
    - More events during weekdays
    - Clustering around maintenance cycles (every ~30 days)
    - Some random scatter
    """
    if np.random.random() < 0.3:
        # Cluster around maintenance cycle
        cycle_day = np.random.choice([30, 60, 90, 120, 150])
        days_ago = cycle_day + np.random.randint(-5, 5)
    else:
        # Random with preference for recent
        days_ago = int(np.random.exponential(scale=40))
        days_ago = min(days_ago, 180)

    # Prefer weekdays
    base_time = datetime.now(timezone.utc) - timedelta(days=int(days_ago))
    while base_time.weekday() >= 5 and np.random.random() < 0.7:
        days_ago += 1
        base_time = datetime.now(timezone.utc) - timedelta(days=int(days_ago))

    # Time of day: prefer business hours
    if np.random.random() < 0.8:
        hour = np.random.randint(7, 18)
    else:
        hour = np.random.randint(0, 24)

    seconds_offset = hour * 3600 + np.random.randint(0, 3600)
    dt = datetime.now(timezone.utc) - timedelta(days=int(days_ago), seconds=int(seconds_offset))

    return dt.isoformat()


def generate():
    cases = []
    case_counter = 1

    # Set seeds for reproducibility
    random.seed(42)
    np.random.seed(42)

    for family in FAMILIES:
        for _ in range(5):
            case_id = f"C-{case_counter:03d}"

            context = generate_context(family.get("constraints", {}))
            metrics = generate_metrics_realistic(family["signals"], family["title"])

            # Full validation
            validate_case({"metrics": metrics}, family["signals"])

            case_record = {
                "case_id": case_id,
                "created_at": generate_timestamp_realistic(),
                "family": family["title"],
                "title": family["title"],
                "context": context,
                "metrics": metrics,
                "signals": family["signals"],
                "matched_signals_template": family["matched_template"],
                "resolution_summary": family["resolution"],
                "next_checks_hint": family["hints"],
            }
            cases.append(case_record)
            case_counter += 1

    return cases


if __name__ == "__main__":
    print("Generating realistic synthetic cases with research-backed distributions...")
    try:
        data = generate()
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[OK] Successfully wrote {len(data)} realistic cases to:\n   {OUTPUT_PATH}")
        print("\nImprovements applied:")
        print("  - Beta distributions for yields (right-skewed, realistic clustering)")
        print("  - Log-normal for variance (multiplicative error patterns)")
        print("  - Poisson for lot counts (discrete event modeling)")
        print("  - Truncated normal for measurement confidence")
        print("  - Correlated metrics (variance<->confidence, change<->rework, etc.)")
        print("  - Temporal clustering (maintenance cycles, weekday preference)")
    except ValueError as e:
        print(f"\n FATAL DATA DEFINITION ERROR:\n{e}")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n FATAL VALIDATION ERROR:\n{e}")
        sys.exit(1)