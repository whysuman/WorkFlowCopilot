import streamlit as st
import datetime as dt

from app.ui.state import init_session_state
from app.ui.intake_form import build_intake_form
from app.ui.output_render import render_outputs
from app.core.payload import build_payload
from app.core.persistence import append_jsonl
from app.rag_pipeline.engine import build_ai_response
from app.rag_pipeline.llm import detect_backend, extract_fields_from_text

from app.config import PERSIST_PATH


def main() -> None:
    st.set_page_config(page_title="AI-Guided Investigation Copilot (v1)", layout="wide")
    init_session_state()

    st.title("AI-Guided Manufacturing Investigation Copilot (v1)")

    left, right = st.columns(2, border=True)

    with left:
        submit, inputs, nlp_free_text = build_intake_form()

        # --- Submit handler ---
        if submit:
            mode = inputs["mode"]
            form_metrics = inputs["form_metrics"]

            if mode == "NLP":
                # NLP mode: extract fields from free text via LLM
                st.session_state.nlp_extraction_error = None
                st.session_state.nlp_extraction_result = None

                if not nlp_free_text.strip():
                    st.session_state.nlp_extraction_error = "Please enter a description of the issue."
                else:
                    backend = detect_backend()
                    if backend == "placeholder":
                        st.session_state.nlp_extraction_error = (
                            "NLP mode requires an LLM backend. "
                            "Set HF_TOKEN for HuggingFace API, or start Ollama for local inference."
                        )
                    else:
                        extracted = extract_fields_from_text(nlp_free_text, backend)
                        if extracted is None:
                            st.session_state.nlp_extraction_error = (
                                "Failed to extract fields from text. Please try again or use Form mode."
                            )
                        else:
                            st.session_state.nlp_extraction_result = extracted

                            # Build payload from extracted fields
                            nlp_metrics = {
                                k: extracted.get(k)
                                for k in [
                                    "yield_pct", "metric_variance", "change_magnitude",
                                    "measurement_confidence", "affected_lot_count",
                                    "rework_rate", "time_window_hours",
                                ]
                            }
                            payload = build_payload(
                                site=extracted.get("site") or inputs["site"],
                                tool_group=extracted.get("tool_group") or inputs["tool_group"],
                                process_step=extracted.get("process_step") or inputs["process_step"],
                                severity=extracted.get("severity") or inputs["severity"],
                                timestamp=inputs["timestamp"],
                                anomaly_summary=extracted.get("anomaly_summary") or nlp_free_text[:200],
                                mode=mode,
                                form_metrics=form_metrics,
                                nlp_metrics=nlp_metrics,
                            )
                            st.session_state.last_request = payload
                            st.session_state.last_response = build_ai_response(payload)

                            append_jsonl(
                                PERSIST_PATH,
                                {
                                    "ts": dt.datetime.now().isoformat(),
                                    "request": st.session_state.last_request,
                                    "response": st.session_state.last_response,
                                    "response_id": st.session_state.last_response.get("meta", {}).get("response_id"),
                                },
                            )

                if st.session_state.nlp_extraction_error:
                    st.error(st.session_state.nlp_extraction_error)

            else:  # Form mode
                payload = build_payload(
                    site=inputs["site"],
                    tool_group=inputs["tool_group"],
                    process_step=inputs["process_step"],
                    severity=inputs["severity"],
                    timestamp=inputs["timestamp"],
                    anomaly_summary=inputs["anomaly_summary"],
                    mode=mode,
                    form_metrics=form_metrics,
                )
                st.session_state.last_request = payload
                st.session_state.last_response = build_ai_response(payload)

                append_jsonl(
                    PERSIST_PATH,
                    {
                        "ts": dt.datetime.now().isoformat(),
                        "request": st.session_state.last_request,
                        "response": st.session_state.last_response,
                        "response_id": st.session_state.last_response.get("meta", {}).get("response_id"),
                    },
                )

    with right:
        render_outputs(st.session_state.last_response)

        # Show LLM backend status
        if st.session_state.last_response:
            meta = st.session_state.last_response.get("meta", {})
            llm_note = meta.get("llm_note")
            if llm_note:
                st.info(llm_note)

    with st.expander("Debug (optional)", expanded=False):
        st.write("mode:", st.session_state.mode)
        st.write("readiness_pct:", st.session_state.readiness_pct)
        st.write("last_request:", st.session_state.last_request)
        st.write("last_response:", st.session_state.last_response)
        if st.session_state.nlp_extraction_result:
            st.write("nlp_extraction_result:", st.session_state.nlp_extraction_result)


if __name__ == "__main__":
    main()
