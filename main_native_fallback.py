"""
AI-Guided Manufacturing Investigation Copilot - Modern UI
Enterprise-grade interface for semiconductor manufacturing anomaly investigation.
"""
import streamlit as st
import datetime as dt

from app.ui.state import init_session_state
from app.ui.styles import inject_custom_css, render_header, render_footer
from app.core.payload import build_payload
from app.core.persistence import append_jsonl
from app.core.readiness import compute_readiness
from app.rag_pipeline.engine import build_ai_response
from app.rag_pipeline.llm import detect_backend, extract_fields_from_text
from app.config import (
    PERSIST_PATH, SITES, TOOL_GROUPS, PROCESS_STEPS, SEVERITY_LEVELS, DEFAULTS
)

SEVERITY_OPTION_LABELS = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
}
SEVERITY_OPTION_KEYS = list(SEVERITY_OPTION_LABELS.keys())
REQUIRED_FIELD_LABELS = {
    "site_selector": "Site Location",
    "tool_group_selector": "Tool Group",
    "process_step_selector": "Process Step",
    "severity_selector": "Issue Severity",
    "yield_pct_required": "Yield (%)",
    "affected_lot_count_required": "Affected Lot Count",
    "time_window_hours_required": "Time Window (hours)",
}
REQUIRED_WIDGET_KEYS = list(REQUIRED_FIELD_LABELS.keys())
HIGHLIGHTABLE_WIDGET_KEYS = REQUIRED_WIDGET_KEYS + ["core_issue_narrative"]


def _has_valid_production_context(
    site: str,
    tool_group: str,
    process_step: str,
    severity: str | None,
) -> bool:
    """Return True only when all production context inputs are valid selections."""
    return (
        site in SITES[1:]
        and tool_group in TOOL_GROUPS[1:]
        and process_step in PROCESS_STEPS[1:]
        and severity in SEVERITY_LEVELS[1:]
    )


def _invalid_required_keys(
    site: str,
    tool_group: str,
    process_step: str,
    severity: str | None,
    yield_pct: float | None,
    affected_lot_count: int | None,
    time_window_hours: int | None,
) -> list[str]:
    """Return widget keys for required fields that are currently invalid."""
    invalid = []
    if site not in SITES[1:]:
        invalid.append("site_selector")
    if tool_group not in TOOL_GROUPS[1:]:
        invalid.append("tool_group_selector")
    if process_step not in PROCESS_STEPS[1:]:
        invalid.append("process_step_selector")
    if severity not in SEVERITY_LEVELS[1:]:
        invalid.append("severity_selector")
    if yield_pct is None:
        invalid.append("yield_pct_required")
    if affected_lot_count is None:
        invalid.append("affected_lot_count_required")
    if time_window_hours is None:
        invalid.append("time_window_hours_required")
    return invalid


def _render_invalid_required_css(invalid_keys: list[str]):
    """Highlight invalid required widgets using their Streamlit key wrapper class."""
    import streamlit as st

    reset_selector_by_key = {
        "site_selector": ['.st-key-site_selector [data-baseweb="select"]'],
        "tool_group_selector": ['.st-key-tool_group_selector [data-baseweb="select"]'],
        "process_step_selector": ['.st-key-process_step_selector [data-baseweb="select"]'],
        "severity_selector": [
            '.st-key-severity_selector [data-baseweb="button-group"]',
            '.st-key-severity_selector [role="radiogroup"]',
        ],
        "yield_pct_required": [
            '.st-key-yield_pct_required [data-testid="stNumberInputContainer"]',
            '.st-key-yield_pct_required [data-testid="stNumberInput"]',
            '.st-key-yield_pct_required [data-baseweb="base-input"]',
            '.st-key-yield_pct_required [data-baseweb="input"]',
            '.st-key-yield_pct_required input',
        ],
        "affected_lot_count_required": [
            '.st-key-affected_lot_count_required [data-testid="stNumberInputContainer"]',
            '.st-key-affected_lot_count_required [data-testid="stNumberInput"]',
            '.st-key-affected_lot_count_required [data-baseweb="base-input"]',
            '.st-key-affected_lot_count_required [data-baseweb="input"]',
            '.st-key-affected_lot_count_required input',
        ],
        "time_window_hours_required": [
            '.st-key-time_window_hours_required [data-testid="stNumberInputContainer"]',
            '.st-key-time_window_hours_required [data-testid="stNumberInput"]',
            '.st-key-time_window_hours_required [data-baseweb="base-input"]',
            '.st-key-time_window_hours_required [data-baseweb="input"]',
            '.st-key-time_window_hours_required input',
        ],
        "core_issue_narrative": ['.st-key-core_issue_narrative [data-baseweb="textarea"]'],
    }

    invalid_selector_by_key = {
        "site_selector": ['.st-key-site_selector [data-baseweb="select"]'],
        "tool_group_selector": ['.st-key-tool_group_selector [data-baseweb="select"]'],
        "process_step_selector": ['.st-key-process_step_selector [data-baseweb="select"]'],
        "severity_selector": [
            '.st-key-severity_selector [data-baseweb="button-group"]',
            '.st-key-severity_selector [role="radiogroup"]',
        ],
        "yield_pct_required": [
            '.st-key-yield_pct_required [data-testid="stNumberInputContainer"]',
        ],
        "affected_lot_count_required": [
            '.st-key-affected_lot_count_required [data-testid="stNumberInputContainer"]',
        ],
        "time_window_hours_required": [
            '.st-key-time_window_hours_required [data-testid="stNumberInputContainer"]',
        ],
        "core_issue_narrative": ['.st-key-core_issue_narrative [data-baseweb="textarea"]'],
    }

    all_reset_selectors = ",\n".join(
        selector
        for key in HIGHLIGHTABLE_WIDGET_KEYS
        for selector in reset_selector_by_key.get(key, [])
    )
    invalid_selectors = ",\n".join(
        selector
        for key in invalid_keys
        for selector in invalid_selector_by_key.get(key, [])
    )

    if not all_reset_selectors:
        return

    invalid_block = ""
    if invalid_selectors:
        invalid_block = f"""
{invalid_selectors} {{
    box-shadow: none !important;
    outline: 2px solid #dc2626 !important;
    outline-offset: 1px !important;
    border-radius: 0.5rem !important;
}}
"""

    st.markdown(
        f"""
<style>
{all_reset_selectors} {{
    box-shadow: none !important;
    outline: none !important;
}}
{invalid_block}
</style>
""",
        unsafe_allow_html=True,
    )


def render_intake_screen():
    """Render the intake form screen using native Streamlit components."""

    st.subheader("Anomaly Intake")
    st.caption("Describe the production issue to trigger AI-driven root cause analysis.")

    # Mode toggle
    mode = st.radio(
        "Input Mode",
        ["Form", "NLP"],
        horizontal=True,
        key="mode",
        label_visibility="collapsed"
    )

    invalid_required_keys = st.session_state.get("invalid_required_keys", [])
    if mode != "Form":
        invalid_required_keys = []
        st.session_state.invalid_required_keys = []
    if invalid_required_keys:
        _render_invalid_required_css(invalid_required_keys)

    with st.form("intake_form"):
        if mode == "Form":
            # === PRODUCTION CONTEXT ===
            st.markdown("**📋 Production Context**")

            col1, col2 = st.columns(2)
            with col1:
                site = st.selectbox("Site Location", SITES, index=0, key="site_selector")
                process_step = st.selectbox("Process Step", PROCESS_STEPS, index=0, key="process_step_selector")
            with col2:
                tool_group = st.selectbox("Tool Group", TOOL_GROUPS, index=0, key="tool_group_selector")
                severity_key = st.segmented_control(
                    "Issue Severity",
                    options=SEVERITY_OPTION_KEYS,
                    format_func=lambda value: SEVERITY_OPTION_LABELS[value],
                    selection_mode="single",
                    default=None,
                    key="severity_selector",
                )
                severity = severity_key

            st.markdown("---")

            # === ISSUE NARRATIVE ===
            st.markdown("**📝 CORE ISSUE NARRATIVE**")

            core_col1, core_col2, core_col3 = st.columns(3)
            with core_col1:
                yield_pct = st.number_input(
                    "Yield (%)", min_value=0.0, max_value=100.0, value=None,
                    placeholder=str(DEFAULTS["yield_pct"]),
                    help="Percentage of products passing quality checks. Normal is around 92%. Below 80% is typically serious.",
                    key="yield_pct_required",
                )
            with core_col2:
                affected_lot_count = st.number_input(
                    "Affected Lot Count", min_value=0, value=None,
                    placeholder=str(DEFAULTS["affected_lot_count"]),
                    help="Number of production lots showing the issue. More lots usually means broader impact.",
                    key="affected_lot_count_required",
                )
            with core_col3:
                time_window_hours = st.number_input(
                    "Time Window (hours)", min_value=1, value=None,
                    placeholder=str(DEFAULTS["time_window_hours"]),
                    help="How long the anomaly has been occurring. Short windows often indicate sudden events.",
                    key="time_window_hours_required",
                )

            anomaly_summary = st.text_area(
                "Detailed Description (Optional)",
                placeholder="e.g., Seeing unexpected particle count spikes on tool chamber B after PM cycle...",
                height=120,
                key="core_issue_narrative",
            )

            # === ADVANCED METRICS (Collapsible) ===
            with st.expander("Add Advanced Telemetry Markers (Reccommended)"):
                met_col1, met_col2 = st.columns(2)
                with met_col1:
                    metric_variance = st.number_input(
                        "Metric Variance", min_value=0.0, value=None,
                        placeholder=str(DEFAULTS["metric_variance"]),
                        help="How unstable the metric is. Higher variance indicates noisier or less stable behavior.",
                    )
                with met_col2:
                    change_magnitude = st.number_input(
                        "Change Magnitude (+/-)", value=None,
                        placeholder=str(DEFAULTS["change_magnitude"]),
                        help="Size of the shift from baseline. Negative values indicate degradation, positive indicates improvement.",
                    )
                    measurement_confidence = st.number_input(
                        "Measurement Confidence (0-1)", min_value=0.0, max_value=1.0, value=None,
                        placeholder=str(DEFAULTS["measurement_confidence"]),
                        help="Confidence in the measurement itself on a 0-1 scale. Lower values suggest instrumentation uncertainty.",
                    )
                    rework_rate = st.number_input(
                        "Rework Rate (%)", min_value=0.0, max_value=100.0, value=None,
                        placeholder=str(DEFAULTS["rework_rate"]),
                        help="Percentage of products requiring rework. Elevated rework can indicate hidden process quality issues.",
                    )

            nlp_free_text = ""
            timestamp = dt.datetime.now()

            form_metrics = {
                "yield_pct": yield_pct if 'yield_pct' in dir() else None,
                "metric_variance": metric_variance if 'metric_variance' in dir() else None,
                "change_magnitude": change_magnitude if 'change_magnitude' in dir() else None,
                "measurement_confidence": measurement_confidence if 'measurement_confidence' in dir() else None,
                "affected_lot_count": affected_lot_count if 'affected_lot_count' in dir() else None,
                "rework_rate": rework_rate if 'rework_rate' in dir() else None,
                "time_window_hours": time_window_hours if 'time_window_hours' in dir() else None,
            }

        else:
            # === NLP MODE ===
            site = SITES[0]
            tool_group = TOOL_GROUPS[0]
            process_step = PROCESS_STEPS[0]
            severity = SEVERITY_LEVELS[0]
            anomaly_summary = ""
            timestamp = dt.datetime.now()
            form_metrics = {}

            st.markdown("**⚡ Natural Language Input**")
            st.info("Describe the issue in plain language. The AI will automatically extract site, tool group, process step, severity, and metrics from your description.")

            nlp_free_text = st.text_area(
                "Free-text description",
                height=200,
                placeholder="Example: Yield dropped to 78% on ETCH-CLUSTER-1 at Plant-A, 12 lots affected over 24 hours, high severity etch issue. Variance is 0.45, change magnitude -8.5, measurement confidence 0.65, rework rate 6.1%.",
            )

        # === SUBMIT SECTION ===
        submitted = st.form_submit_button(
            "🔍 Submit Diagnosis",
            use_container_width=True,
            type="primary",
        )

    # Compute and display readiness
    nlp_text_present = len(nlp_free_text.strip()) >= 30 if mode == "NLP" else False
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
    )

    # Readiness bar with status
    st.progress(readiness_pct / 100)
    if readiness_pct < 40:
        st.caption(f"Readiness: {readiness_pct}% — Add more context for better guidance")
    elif readiness_pct < 70:
        st.caption(f"Readiness: {readiness_pct}% — Partial context")
    else:
        st.caption(f"Readiness: {readiness_pct}% — Ready for analysis")

    return submitted, {
        "site": site,
        "tool_group": tool_group,
        "process_step": process_step,
        "severity": severity,
        "timestamp": timestamp,
        "anomaly_summary": anomaly_summary,
        "mode": mode,
        "form_metrics": form_metrics,
    }, nlp_free_text


def render_results_screen(response: dict):
    """Render the results screen using native Streamlit components."""

    if not response:
        st.info("Submit an investigation to see AI-powered diagnosis results.")
        return

    # --- NLP Extracted Fields (if available) ---
    nlp_result = st.session_state.get("nlp_extraction_result")
    if nlp_result:
        with st.expander("📤 Extracted Fields (NLP)", expanded=False):
            col_ctx, col_met = st.columns(2)
            with col_ctx:
                st.markdown("**Context**")
                st.write(f"Site: {nlp_result.get('site') or '—'}")
                st.write(f"Tool group: {nlp_result.get('tool_group') or '—'}")
                st.write(f"Process step: {nlp_result.get('process_step') or '—'}")
                st.write(f"Severity: {nlp_result.get('severity') or '—'}")
                summary = nlp_result.get("anomaly_summary") or "—"
                st.write(f"Summary: {summary[:100]}{'...' if len(summary) > 100 else ''}")
            with col_met:
                st.markdown("**Metrics**")
                metric_labels = {
                    "yield_pct": "Yield (%)",
                    "metric_variance": "Variance",
                    "change_magnitude": "Change magnitude",
                    "measurement_confidence": "Confidence",
                    "affected_lot_count": "Affected lots",
                    "rework_rate": "Rework rate (%)",
                    "time_window_hours": "Time window (hrs)",
                }
                for key, label in metric_labels.items():
                    val = nlp_result.get(key)
                    st.write(f"{label}: {val if val is not None else '—'}")

    assessment = response.get("assessment", {})
    meta = response.get("meta", {})

    # === BACK BUTTON ===
    if st.button("← New Diagnosis"):
        st.session_state.last_response = None
        st.rerun()

    # === MAIN RESULTS ===
    pattern = assessment.get("pattern", "Analysis Complete")
    priority = assessment.get("priority", "Medium")
    confidence = assessment.get("confidence", "Medium")
    confidence_pct = {"High": 94, "Medium": 72, "Low": 45}.get(confidence, 70)

    # Priority colors
    priority_colors = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    priority_icon = priority_colors.get(priority, "⚪")

    st.markdown("---")

    # Diagnosis header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 🎯 {pattern}")
        st.caption(assessment.get("diagnostic_approach", "AI-generated diagnostic recommendation"))
    with col2:
        st.metric("Priority", f"{priority_icon} {priority}")

    # Confidence and status
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Confidence Score", f"{confidence_pct}%")
        st.progress(confidence_pct / 100)
    with col2:
        st.success("✓ Validated Pattern")

    st.markdown("---")

    # === AI NARRATIVE ===
    narrative = response.get("narrative", "")
    if narrative:
        st.markdown("**📄 AI Narrative**")
        st.write(narrative)
        st.markdown("---")

    # === RECOMMENDED ACTIONS ===
    checks = response.get("next_checks", [])
    if checks:
        st.markdown("**✅ Immediate Action Plan**")
        for i, check in enumerate(checks, 1):
            category = check.get("category", "")
            with st.container(border=True):
                col1, col2 = st.columns([1, 20])
                with col1:
                    st.markdown(f"**{i}**")
                with col2:
                    if category:
                        st.caption(category.upper())
                    st.markdown(f"**{check.get('check', '')}**")
                    st.caption(check.get("why", ""))

    # === SIMILAR CASES ===
    st.markdown("---")
    st.markdown("**📚 Similar Historical Cases**")

    # Show no-match note if present
    note = response.get("no_strong_match_note")
    if note:
        st.info(note)

    cases = response.get("similar_cases", [])
    if cases:
        for case in cases:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{case.get('case_id', 'Case')}** - {case.get('family', '')}")
                    matched = case.get("matched_signals", "")
                    if matched:
                        st.caption(f"Matched signals: {matched}")
                    st.caption(f"Resolution: {case.get('resolution', 'N/A')}")
                with col2:
                    score = case.get("similarity_score", "")
                    st.metric("Match", case.get("similarity", ""), score)
    elif not note:
        st.write("No similar cases found.")

    # === ESCALATION SUMMARY ===
    escalation = response.get("escalation_summary", "")
    if escalation:
        st.markdown("---")
        st.markdown("**⚠️ Escalation Summary**")
        st.warning(escalation)

    # === ASSESSMENT REASONING ===
    reasoning = assessment.get("reasoning", "")
    source = assessment.get("source", "")
    if reasoning or source:
        with st.expander("🔬 Assessment Details"):
            if reasoning:
                st.write(reasoning)
            if source:
                source_label = "LLM-generated" if source == "llm" else "Rule-based heuristics"
                st.caption(f"Assessment source: {source_label}")

    # === DIAGNOSTICS METADATA ===
    with st.expander("⚙️ Diagnostics Metadata"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Backend", meta.get("backend", "unknown"))
        with col2:
            st.metric("RAG Cases", meta.get("rag_cases_retrieved", 0))
        with col3:
            timings = meta.get("timings", {})
            st.metric("Latency", f"{timings.get('total_ms', 0)}ms")

        st.caption(f"Model: {meta.get('model', 'N/A')}")
        st.caption(f"Response ID: {meta.get('response_id', 'N/A')}")

        # Detailed timings
        if timings:
            rag_ms = timings.get("rag_retrieval_ms", 0)
            llm_ms = timings.get("llm_generation_ms", 0)
            st.caption(f"Breakdown: RAG {rag_ms}ms | LLM {llm_ms}ms")

        # Cache indicator
        if meta.get("from_cache"):
            st.caption("(Response from cache)")


def main():
    st.set_page_config(
        page_title="Diagnostic AI - Manufacturing Portal",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    init_session_state()
    inject_custom_css()
    render_header()

    # Main content area
    if st.session_state.last_response:
        # Show results screen
        render_results_screen(st.session_state.last_response)
    else:
        # Show intake screen
        submitted, inputs, nlp_free_text = render_intake_screen()

        if submitted:
            mode = inputs["mode"]
            can_submit = True

            if mode == "Form":
                invalid_keys = _invalid_required_keys(
                    site=inputs["site"],
                    tool_group=inputs["tool_group"],
                    process_step=inputs["process_step"],
                    severity=inputs["severity"],
                    yield_pct=inputs["form_metrics"].get("yield_pct"),
                    affected_lot_count=inputs["form_metrics"].get("affected_lot_count"),
                    time_window_hours=inputs["form_metrics"].get("time_window_hours"),
                )
                if invalid_keys:
                    st.session_state.invalid_required_keys = invalid_keys
                    _render_invalid_required_css(invalid_keys)
                    invalid_labels = [
                        REQUIRED_FIELD_LABELS[key]
                        for key in invalid_keys
                        if key in REQUIRED_FIELD_LABELS
                    ]
                    st.error(
                        "Cannot submit until all required fields are valid. "
                        + "Missing/invalid: "
                        + ", ".join(invalid_labels)
                    )
                    can_submit = False
                else:
                    st.session_state.invalid_required_keys = []

            if can_submit and mode == "Form" and not _has_valid_production_context(
                site=inputs["site"],
                tool_group=inputs["tool_group"],
                process_step=inputs["process_step"],
                severity=inputs["severity"],
            ):
                st.error(
                    "Cannot submit until all Production Context fields have valid selections."
                )
            elif can_submit:
                # Show loading state
                with st.spinner("Processing Diagnostic Pipeline..."):
                    if mode == "NLP":
                        if not nlp_free_text.strip():
                            st.error("Please enter a description of the issue.")
                        else:
                            backend = detect_backend()
                            if backend == "placeholder":
                                st.error("NLP mode requires an LLM backend. Set HF_TOKEN or start Ollama.")
                            else:
                                extracted = extract_fields_from_text(nlp_free_text, backend)
                                if extracted is None:
                                    st.error("Failed to extract fields. Please try again or use Form mode.")
                                else:
                                    st.session_state.nlp_extraction_result = extracted
                                    nlp_metrics = {
                                        k: extracted.get(k)
                                        for k in ["yield_pct", "metric_variance", "change_magnitude",
                                                  "measurement_confidence", "affected_lot_count",
                                                  "rework_rate", "time_window_hours"]
                                    }
                                    payload = build_payload(
                                        site=extracted.get("site") or inputs["site"],
                                        tool_group=extracted.get("tool_group") or inputs["tool_group"],
                                        process_step=extracted.get("process_step") or inputs["process_step"],
                                        severity=extracted.get("severity") or inputs["severity"],
                                        timestamp=inputs["timestamp"],
                                        anomaly_summary=extracted.get("anomaly_summary") or nlp_free_text[:200],
                                        mode=mode,
                                        form_metrics=inputs["form_metrics"],
                                        nlp_metrics=nlp_metrics,
                                    )
                                    st.session_state.last_request = payload
                                    st.session_state.last_response = build_ai_response(payload)
                                    append_jsonl(PERSIST_PATH, {
                                        "ts": dt.datetime.now().isoformat(),
                                        "request": payload,
                                        "response": st.session_state.last_response,
                                    })
                                    st.rerun()
                    else:
                        payload = build_payload(
                            site=inputs["site"],
                            tool_group=inputs["tool_group"],
                            process_step=inputs["process_step"],
                            severity=inputs["severity"],
                            timestamp=inputs["timestamp"],
                            anomaly_summary=inputs["anomaly_summary"],
                            mode=mode,
                            form_metrics=inputs["form_metrics"],
                        )
                        st.session_state.last_request = payload
                        st.session_state.last_response = build_ai_response(payload)
                        append_jsonl(PERSIST_PATH, {
                            "ts": dt.datetime.now().isoformat(),
                            "request": payload,
                            "response": st.session_state.last_response,
                        })
                        st.rerun()

    render_footer()


if __name__ == "__main__":
    main()
