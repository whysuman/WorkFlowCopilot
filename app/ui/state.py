import streamlit as st

def init_session_state() -> None:
    """Initialize session state keys exactly once."""
    if "mode" not in st.session_state:
        st.session_state.mode = "Form"  # "Form" | "NLP"
    if "last_request" not in st.session_state:
        st.session_state.last_request = None
    if "last_response" not in st.session_state:
        st.session_state.last_response = None
    if "readiness_pct" not in st.session_state:
        st.session_state.readiness_pct = 0
    if "nlp_extraction_result" not in st.session_state:
        st.session_state.nlp_extraction_result = None
    if "nlp_extraction_error" not in st.session_state:
        st.session_state.nlp_extraction_error = None
