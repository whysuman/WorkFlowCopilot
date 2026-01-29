import streamlit as st

def init_session_state() -> None:
    """Initialize session state keys exactly once."""
    if "mode" not in st.session_state:
        st.session_state.mode = "Form"  # "Form" | "JSON"
    if "last_request" not in st.session_state:
        st.session_state.last_request = None
    if "last_response" not in st.session_state:
        st.session_state.last_response = None
    if "json_validation_error" not in st.session_state:
        st.session_state.json_validation_error = None
    if "readiness_pct" not in st.session_state:
        st.session_state.readiness_pct = 0
    if "last_json_valid_on_submit" not in st.session_state:
        st.session_state.last_json_valid_on_submit = None
    if "show_json_metrics" not in st.session_state:
        st.session_state.show_json_metrics = False