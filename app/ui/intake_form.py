import streamlit as st
import datetime as dt
from typing import Any, Dict, Tuple

from app.config import SITES, TOOL_GROUPS, PROCESS_STEPS, SEVERITY_LEVELS, DEFAULTS
from app.core.readiness import compute_readiness
from app.ui.output_render import render_readiness


def build_intake_form() -> Tuple[bool, Dict[str, Any], str]:
    """
    Renders the entire LEFT column intake form (single st.form) with 3 expanders:
      - Context (expanded)
      - Core (collapsed)
      - Advanced (collapsed)

    Returns:
      submit_clicked: bool
      inputs: dict with context/core/advanced + mode + form_metrics
      nlp_free_text: str (empty if mode != "NLP")
    """
    st.radio(
        "Metrics input mode",
        ["Form", "NLP"],
        horizontal=True,
        key="mode"
    )
    mode = st.session_state.mode  # persist across reruns

    with st.form("input_form"):
        # ---------- Expanders ----------
        yield_pct = affected_lot_count = time_window_hours = None
        metric_variance = change_magnitude = measurement_confidence = rework_rate = None
        site = SITES[0]
        tool_group = TOOL_GROUPS[0]
        process_step = PROCESS_STEPS[0]
        severity = SEVERITY_LEVELS[0]
        timestamp = dt.datetime.now()
        anomaly_summary = ""
        nlp_free_text = ""

        if mode == "Form":
            with st.expander("Context", expanded=True):
                st.caption("Where and how the issue is occurring.")
                site = st.selectbox("Site", SITES, index=0, help="Which manufacturing facility reported the issue")
                tool_group = st.selectbox("Tool group", TOOL_GROUPS, index=0, help="The specific machine cluster involved (e.g. etch tools, lithography tools)")
                process_step = st.selectbox("Process step", PROCESS_STEPS, index=0, help="Which manufacturing step the issue occurred in")
                severity = st.selectbox("Severity", SEVERITY_LEVELS, index=0, help="How urgent this is based on production impact")
                timestamp = st.datetime_input("Timestamp", value=dt.datetime.now(), help="When the issue was first observed")

            with st.expander("Core", expanded=False):
                st.caption(
                    "Minimum information required to analyze the issue. "
                    "These signals describe the problem and its impact."
                )
                anomaly_summary = st.text_area(
                    "Anomaly summary",
                    placeholder="What changed, when did it start, and how was it detected?",
                    height=120,
                    help="Describe what changed, when it started, and how it was detected. The AI uses this to find similar historical cases.",
                )
                yield_pct = st.number_input(
                    "Yield (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=None,
                    placeholder=float(DEFAULTS["yield_pct"]),
                    step=0.1,
                    help="Percentage of products passing quality checks. Normal is ~92%. Below 80% is a serious problem.",
                )
                affected_lot_count = st.number_input(
                    "Affected lot count",
                    min_value=0,
                    value=None,
                    placeholder=int(DEFAULTS["affected_lot_count"]),
                    step=1,
                    help="Number of production batches showing the issue. More lots = wider impact.",
                )
                time_window_hours = st.number_input(
                    "Time window (hours)",
                    min_value=1,
                    value=None,
                    placeholder=int(DEFAULTS["time_window_hours"]),
                    step=1,
                    help="How long the anomaly has been occurring. Short (<12h) = sudden event; long (>48h) = gradual drift.",
                )

            with st.expander("Advanced", expanded=False):
                st.caption(
                    "Optional signals that improve confidence and precision. "
                    "Analysis can proceed without these."
                )
                metric_variance = st.number_input(
                    "Metric variance (>= 0)",
                    min_value=0.0,
                    value=None,
                    placeholder=float(DEFAULTS["metric_variance"]),
                    step=0.01,
                    help="How unstable the measurements are. 0 = perfectly stable, >0.36 = very noisy.",
                )
                change_magnitude = st.number_input(
                    "Change magnitude (+/-)",
                    value=None,
                    placeholder=float(DEFAULTS["change_magnitude"]),
                    step=0.1,
                    help="How much the metric shifted from normal. Negative = got worse, positive = improved.",
                )
                measurement_confidence = st.number_input(
                    "Measurement confidence (0-1)",
                    min_value=0.0,
                    max_value=1.0,
                    value=None,
                    placeholder=float(DEFAULTS["measurement_confidence"]),
                    step=0.01,
                    help="How trustworthy the measurement is. 0-1 scale. Below 0.5 = unreliable, above 0.8 = high confidence.",
                )
                rework_rate = st.number_input(
                    "Rework rate (%) (0-100)",
                    min_value=0.0,
                    max_value=100.0,
                    value=None,
                    placeholder=float(DEFAULTS["rework_rate"]),
                    step=0.1,
                    help="Percentage of products that need to be fixed/reprocessed. Normal is <2%, above 8% is serious.",
                )

        else:
            # NLP mode: single free-text textarea
            st.markdown("**Describe the manufacturing issue in plain language.**")
            st.caption(
                "The AI will extract site, tool group, process step, severity, metrics, "
                "and anomaly summary from your description. An LLM backend is required."
            )
            nlp_free_text = st.text_area(
                "Free-text investigation description",
                height=280,
                placeholder=(
                    "Example: Yield dropped to 78% on ETCH-CLUSTER-1 at Plant-A, "
                    "12 lots affected over 24 hours, high severity etch issue. "
                    "Variance is 0.45, change magnitude -8.5, measurement confidence 0.65, "
                    "rework rate 6.1%."
                ),
            )

        # Build form_metrics dict (used in Form mode; ignored in NLP mode)
        form_metrics = {
            "yield_pct": yield_pct,
            "metric_variance": metric_variance,
            "change_magnitude": change_magnitude,
            "measurement_confidence": measurement_confidence,
            "affected_lot_count": affected_lot_count,
            "rework_rate": rework_rate,
            "time_window_hours": time_window_hours,
        }

        # --- Readiness ---
        nlp_text_present = (mode == "NLP") and (len(nlp_free_text.strip()) >= 30)
        readiness_pct = compute_readiness(
            site=site,
            tool_group=tool_group,
            process_step=process_step,
            severity=severity,
            timestamp=timestamp,
            anomaly_summary=anomaly_summary,
            mode=mode,
            form_metrics=form_metrics,
            nlp_text_present=nlp_text_present,
            anomaly_min_chars=10,
        )
        st.session_state.readiness_pct = readiness_pct

        st.markdown("**Intake readiness**")
        render_readiness(readiness_pct)

        # --- Submit control ---
        st.caption(f"Submitting metrics from: **{mode}**")
        submit_clicked = st.form_submit_button("Submit investigation")

    inputs: Dict[str, Any] = {
        "site": site,
        "tool_group": tool_group,
        "process_step": process_step,
        "severity": severity,
        "timestamp": timestamp,
        "anomaly_summary": anomaly_summary,
        "mode": mode,
        "form_metrics": form_metrics,
    }
    return submit_clicked, inputs, nlp_free_text
