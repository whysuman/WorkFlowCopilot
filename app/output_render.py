import streamlit as st
from typing import Optional, Dict, Any

def render_readiness(pct: int) -> None:
    """Single overall readiness bar + subtle status."""
    st.progress(pct / 100)

    if pct < 40:
        st.error("Limited context (readiness < 40%). Submission is allowed, but add signals for better guidance.")
    elif pct < 70:
        st.warning("Partial context (40–70%). Add missing signals to improve confidence.")
    else:
        st.success("Sufficient context (> 70%). Ready for meaningful guidance.")


def render_outputs(last_response: Optional[Dict[str, Any]]) -> None:
    """Right column output sections in strict order."""
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
                    st.markdown(f"**Case {i} — Similarity: {c.get('similarity', 'Low')}**")
                    st.write(f"Matched signals: {c.get('matched_signals', '')}")
                    st.write(f"Resolution: {c.get('resolution', '')}")

    st.subheader("Next checks")
    if not last_response:
        st.write("Next checks will appear here after analysis.")
    else:
        checks = last_response.get("next_checks", [])
        if len(checks) < 2:
            st.warning("Expected at least 2 checks; placeholder response is incomplete.")
        for chk in checks:
            with st.container(border=True):
                st.markdown(f"**{chk.get('category', 'Check')}**")
                st.write(chk.get("check", ""))
                st.caption(chk.get("why", ""))

    st.subheader("Escalation summary")
    if not last_response:
        st.write("Escalation summary will appear here after analysis.")
    else:
        st.text(last_response.get("escalation_summary", ""))

    st.subheader("AI narrative")
    if not last_response:
        st.write("LLM synthesis placeholder (v1.5).")
    else:
        st.write(last_response.get("narrative", ""))

