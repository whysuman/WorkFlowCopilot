import streamlit as st
from typing import Optional, Dict, Any

def render_readiness(pct: int) -> None:
    """Single overall readiness bar + subtle status."""
    st.progress(pct / 100)

    if pct < 40:
        st.error("Limited context (readiness < 40%). Submission is allowed, but add signals for better guidance.")
    elif pct < 70:
        st.warning("Partial context (40-70%). Add missing signals to improve confidence.")
    else:
        st.success("Sufficient context (> 70%). Ready for meaningful guidance.")


def render_outputs(last_response: Optional[Dict[str, Any]]) -> None:
    """Right column output sections in strict order."""

    # --- Investigation Assessment ---
    st.subheader("Investigation assessment")
    if not last_response:
        st.write("Assessment will appear here after analysis.")
    else:
        assessment = last_response.get("assessment")
        if assessment:
            col1, col2, col3 = st.columns(3)
            with col1:
                priority = assessment.get("priority", "Unknown")
                priority_colors = {
                    "Critical": "red", "High": "orange",
                    "Medium": "blue", "Low": "green",
                }
                color = priority_colors.get(priority, "gray")
                st.markdown(f"**Priority:** :{color}[{priority}]")
            with col2:
                st.markdown(f"**Pattern:** {assessment.get('pattern', 'Unknown')}")
            with col3:
                confidence = assessment.get("confidence", "Unknown")
                conf_colors = {"High": "green", "Medium": "orange", "Low": "red"}
                conf_color = conf_colors.get(confidence, "gray")
                st.markdown(f"**Confidence:** :{conf_color}[{confidence}]")

            approach = assessment.get("diagnostic_approach", "")
            if approach:
                st.info(f"**Diagnostic approach:** {approach}")
            st.caption(assessment.get("reasoning", ""))
            source = assessment.get("source", "unknown")
            st.caption(f"Assessment source: {'LLM' if source == 'llm' else 'Rule-based'}")
        else:
            st.write("No assessment available.")

    # --- Similar Cases ---
    st.subheader("Similar cases")
    if not last_response:
        st.write("Submit an investigation to view similar historical cases.")
    else:
        note = last_response.get("no_strong_match_note")
        if note:
            st.info(note)

        cases = last_response.get("similar_cases", [])
        if not cases:
            st.write("No similar cases to display.")
        else:
            for i, c in enumerate(cases, 1):
                with st.container(border=True):
                    case_id = c.get("case_id", "")
                    family = c.get("family", "")
                    score = c.get("similarity_score", "")

                    header = f"**Case {i}"
                    if case_id:
                        header += f" ({case_id})"
                    header += f" -- Similarity: {c.get('similarity', 'Low')}"
                    if score:
                        header += f" ({score})"
                    header += "**"
                    st.markdown(header)

                    if family:
                        st.caption(f"Pattern: {family}")
                    st.write(f"Matched signals: {c.get('matched_signals', '')}")
                    st.write(f"Resolution: {c.get('resolution', '')}")

    # --- Next Checks ---
    st.subheader("Next checks")
    if not last_response:
        st.write("Next checks will appear here after analysis.")
    else:
        checks = last_response.get("next_checks", [])
        if len(checks) < 2:
            st.warning("Expected at least 2 checks; response may be incomplete.")
        for chk in checks:
            with st.container(border=True):
                st.markdown(f"**{chk.get('category', 'Check')}**")
                st.write(chk.get("check", ""))
                st.caption(chk.get("why", ""))

    # --- Escalation Summary ---
    st.subheader("Escalation summary")
    if not last_response:
        st.write("Escalation summary will appear here after analysis.")
    else:
        st.text(last_response.get("escalation_summary", ""))

    # --- AI Narrative ---
    st.subheader("AI narrative")
    if not last_response:
        st.write("AI synthesis will appear here after analysis.")
    else:
        st.write(last_response.get("narrative", ""))

    # --- Backend Indicator ---
    meta = last_response.get("meta", {}) if last_response else {}
    backend = meta.get("backend", "")
    if backend:
        backend_labels = {
            "huggingface": "HuggingFace Inference API",
            "ollama": "Ollama (local)",
            "placeholder": "Heuristic (no LLM)",
        }
        label = backend_labels.get(backend, backend)
        model = meta.get("model", "")
        rag_count = meta.get("rag_cases_retrieved", 0)
        parts = [f"Backend: {label}"]
        if model:
            parts.append(f"Model: {model}")
        parts.append(f"RAG cases: {rag_count}")
        st.caption(" | ".join(parts))
