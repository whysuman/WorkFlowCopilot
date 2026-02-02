import streamlit as st
import datetime as dt
import json

from app.ui.state import init_session_state
from app.ui.intake_form import build_intake_form
from app.ui.output_render import render_outputs
from app.core.validation import validate_metrics_json
from app.core.payload import build_payload
from app.core.persistence import append_jsonl
from app.rag_pipeline.engine import build_ai_response

from app.config import PERSIST_PATH, DEFAULTS


def main() -> None:
    st.set_page_config(page_title="AI-Guided Investigation Copilot (v1)", layout="wide")
    init_session_state()


    st.session_state.setdefault("json_example", json.dumps(DEFAULTS, indent=2))

    st.title("AI-Guided Manufacturing Investigation Copilot (v1)")

    left, right = st.columns(2, border=True)

    with left:
        submit, inputs, metrics_json_raw = build_intake_form()

        # Inline error display (only after submit attempts)
        if st.session_state.json_validation_error:
            st.error(st.session_state.json_validation_error)

        # --- Submit handler (the ONLY place JSON validation happens) ---
        if submit:
            st.session_state.json_validation_error = None

            mode = inputs["mode"]
            form_metrics = inputs["form_metrics"]

            # Active mode wins
            if mode == "JSON":
                parsed, err = validate_metrics_json(metrics_json_raw)
                st.session_state.last_json_valid_on_submit = (err is None)
                if err:
                    st.session_state.json_validation_error = err
                else:
                    payload = build_payload(
                        site=inputs["site"],
                        tool_group=inputs["tool_group"],
                        process_step=inputs["process_step"],
                        severity=inputs["severity"],
                        timestamp=inputs["timestamp"],
                        anomaly_summary=inputs["anomaly_summary"],
                        mode=mode,
                        form_metrics=form_metrics,
                        json_metrics=parsed,
                    )
                    st.session_state.last_request = payload
                    st.session_state.last_json_valid_on_submit = True
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
                    json_metrics=None,
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

    with st.expander("Debug (optional)", expanded=False):
        st.write("mode:", st.session_state.mode)
        st.write("readiness_pct:", st.session_state.readiness_pct)
        st.write("last_request:", st.session_state.last_request)
        st.write("last_response:", st.session_state.last_response)


if __name__ == "__main__":
    main()