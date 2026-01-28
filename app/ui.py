import streamlit as st
import datetime as dt
from typing import Any, Dict, Tuple

from app.config import SITES, TOOL_GROUPS, PROCESS_STEPS, SEVERITY_LEVELS, DEFAULTS
from app.readiness import compute_readiness
from app.output_render import render_readiness


def build_intake_form() -> Tuple[bool, Dict[str, Any], str]:
    """
    Renders the entire LEFT column intake form (single st.form) with 3 expanders:
      - Context (expanded)
      - Core (collapsed)
      - Advanced (collapsed)

    Returns:
      submit_clicked: bool
      inputs: dict with context/core/advanced + mode + form_metrics
      metrics_json_raw: str (empty if mode != "JSON")

    IMPORTANT (locked):
      - JSON validation is NOT performed here (validate only on submit in main.py)
      - Readiness in JSON mode uses "textarea non-empty" as the proxy for metrics completeness.
    """
    mode = st.radio(
        "Metrics input mode",
        ["Form", "JSON"],
        horizontal=True,
        index=0 if st.session_state.mode == "Form" else 1,
    )
    st.session_state.mode = mode  # persist across reruns
    with st.form("input_form"):
        # --- Metrics input mode (Mode C) ---


        # ---------- Expanders ----------
        with st.expander("Context", expanded=True):
            st.caption("Where and how the issue is occurring.")
            site = st.selectbox("Site", SITES, index=0)
            tool_group = st.selectbox("Tool group", TOOL_GROUPS, index=0)
            process_step = st.selectbox("Process step", PROCESS_STEPS, index=0)
            severity = st.selectbox("Severity", SEVERITY_LEVELS, index=0)
            timestamp = st.datetime_input("Timestamp", value=dt.datetime.now())

        with st.expander("Core", expanded=False):
            st.caption(
                "Minimum information required to analyze the issue. "
                "These signals describe the problem and its impact."
            )
            anomaly_summary = st.text_area(
                "Anomaly summary",
                placeholder="What changed, when did it start, and how was it detected?",
                height=120,
            )

            # NOTE: Some Streamlit versions may not accept value=None in number_input.
            # If yours errors, switch to numeric defaults and track "touched" later.
            yield_pct = st.number_input(
                "Yield (%)",
                min_value=0.0,
                max_value=100.0,
                value=None,
                placeholder=float(DEFAULTS["yield_pct"]),
                step=0.1,
            )
            affected_lot_count = st.number_input(
                "Affected lot count",
                min_value=0,
                value=None,
                placeholder=int(DEFAULTS["affected_lot_count"]),
                step=1,
            )
            time_window_hours = st.number_input(
                "Time window (hours)",
                min_value=1,
                value=None,
                placeholder=int(DEFAULTS["time_window_hours"]),
                step=1,
            )

        with st.expander("Advanced", expanded=False):
            st.caption(
                "Optional signals that improve confidence and precision. "
                "Analysis can proceed without these."
            )
            metric_variance = st.number_input(
                "Metric variance (≥ 0)",
                min_value=0.0,
                value=None,
                placeholder=float(DEFAULTS["metric_variance"]),
                step=0.01,
            )
            change_magnitude = st.number_input(
                "Change magnitude (+/-)",
                value=None,
                placeholder=float(DEFAULTS["change_magnitude"]),
                step=0.1,
            )
            measurement_confidence = st.number_input(
                "Measurement confidence (0-1)",
                min_value=0.0,
                max_value=1.0,
                value=None,
                placeholder=float(DEFAULTS["measurement_confidence"]),
                step=0.01,
            )
            rework_rate = st.number_input(
                "Rework rate (%) (0-100)",
                min_value=0.0,
                max_value=100.0,
                value=None,
                placeholder=float(DEFAULTS["rework_rate"]),
                step=0.1,
            )

        # --- JSON mode textarea (UI only; NO validation here) ---
        metrics_json_raw = ""
        if mode == "JSON":
            if st.session_state.last_json_valid_on_submit is False:
                st.warning("Previous JSON was invalid. Please correct before submitting.")
            else:
                st.success("Previous JSON was valid.")
                st.markdown("**Metrics (JSON)**")
                st.caption("Strict schema + numeric types. Validation happens only on Submit.")
            metrics_json_raw = st.text_area(
                "Paste metrics JSON",
                height=220,
                placeholder=st.session_state.get("json_example", ""),
        )
        else:
            st.caption("Submitting metrics from: **Form** (JSON will be ignored).")

        # Build form_metrics dict (even if mode == JSON; main.py will ignore them)
        form_metrics = {
            "yield_pct": yield_pct,
            "metric_variance": metric_variance,
            "change_magnitude": change_magnitude,
            "measurement_confidence": measurement_confidence,
            "affected_lot_count": affected_lot_count,
            "rework_rate": rework_rate,
            "time_window_hours": time_window_hours,
        }

        # --- Readiness (no JSON validation pre-submit) ---
        json_metrics_present = (mode == "JSON") and (metrics_json_raw.strip() != "")
        readiness_pct = compute_readiness(
            site=site,
            tool_group=tool_group,
            process_step=process_step,
            severity=severity,
            timestamp=timestamp,
            anomaly_summary=anomaly_summary,
            mode=mode,
            form_metrics=form_metrics,
            json_metrics_present=json_metrics_present,  # NOTE: readiness.py should use this (not "valid")
            anomaly_min_chars=10,  # raise threshold (locked improvement)
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
    return submit_clicked, inputs, metrics_json_raw