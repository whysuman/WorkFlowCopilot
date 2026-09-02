# Manufacturing Investigation Copilot

A tool that helps process engineers work through manufacturing anomalies. You
describe what went wrong (yield dropped, variance spiked, a tool group started
producing scrap), and it pulls up similar past cases, tells you what kind of
problem it looks like, and gives you a list of things to check next.

It is built around a set of 50 historical investigation cases covering ten
common failure patterns in semiconductor fabs. Those cases are the reference
material the system searches against.

There are two ways to use it: a Streamlit app for people, and a REST API for
Power Apps or anything else that speaks HTTP.

## What it actually does

You fill in the site, tool group, process step, severity, and the metrics you
have (yield percentage, affected lots, time window, variance, and so on). You
can also just type a paragraph describing the problem and let the model pull
the fields out of it.

From there:

1. The text is embedded and matched against the case library in ChromaDB.
   Matches below a similarity floor are dropped, so a weak match shows up as
   "no strong match" rather than a misleading suggestion.
2. An LLM writes the narrative, the next checks, and the escalation summary,
   using the retrieved cases as context.
3. It also classifies the problem: which pattern it fits, how urgent it is, how
   confident the system is, and how to approach the diagnosis.

If the LLM is unreachable, the pipeline falls back to rule-based logic and
still returns an assessment. It does not fail the request.

The ten patterns it recognizes are things like unreliable measurements, a
single machine group producing defects, gradual drift, fallout from a
configuration change, false alarms, hidden rework problems, batch-to-batch
variation, noisy data masking a real decline, sudden tool failure, and wear
approaching a maintenance threshold.

## LLM backends

It tries three things in order and uses the first one that works:

1. HuggingFace Inference API, if `HF_TOKEN` is set. Uses
   `Qwen/Qwen2.5-72B-Instruct`.
2. A local Ollama server on port 11434, running `llama3.2:3b`.
3. A placeholder response with rule-based assessment, which needs nothing
   external.

So the app runs with no API key and no local model. You just get less detail in
the narrative.

## Running it

There is no `pyproject.toml` in the repo (it is gitignored), so install the
dependencies yourself:

```
pip install streamlit fastapi uvicorn chromadb sentence-transformers \
    pydantic tenacity python-dotenv huggingface_hub httpx numpy scipy
```

The Streamlit app:

```
streamlit run main.py
```

`main_native_fallback.py` is the same app without the custom CSS, for when the
styled version breaks on a different Streamlit version.

The API:

```
uvicorn api.main:app --reload --port 8000
```

Swagger UI is at `http://localhost:8000/docs`.

First run downloads the embedding model (`BAAI/bge-small-en-v1.5`, around
130MB) and builds the ChromaDB collection under `data/chroma_db/`. After that
it loads from disk.

For a HuggingFace token, put it in a `.env` file at the project root:

```
HF_TOKEN=your_token_here
```

## API endpoints

All under `/api/v1`:

- `POST /investigate` is the main one. It takes the context and metrics, returns
  similar cases, next checks, narrative, escalation summary, and assessment.
- `POST /extract` takes free text and returns the structured fields it could
  pull out.
- `GET /config` returns the dropdown options (sites, tool groups, process steps,
  severity levels). Useful for building a front end without hardcoding them.
- `GET /health` returns status, whether the case library loaded, which LLM backend
  is active.

## Layout

```
main.py                     Streamlit app
main_native_fallback.py     Same app, no custom CSS
app/config.py               Dropdown options, thresholds, model settings
app/core/                   Payload building, validation, persistence, models
app/rag_pipeline/
    rag.py                  ChromaDB retrieval over the case library
    llm.py                  Backend detection and generation
    engine.py               Orchestrates the whole pipeline
    triage.py               Rule-based assessment fallback
    placeholder.py          Response when no LLM is available
app/ui/                     Streamlit form, output rendering, styles
api/                        FastAPI app, routers, request/response models
data/realistic_cases.json   The 50-case reference library
scripts/generate_data.py    Regenerates the case data
tests/test_pipeline.py      Step-by-step pipeline check
docs/                       Power Apps integration guide
```

## Notes

- Requests and responses get appended to `output/requests_responses.jsonl`.
- Responses are cached by a hash of the payload, so resubmitting the same
  inputs does not re-run the pipeline.
- The bucket thresholds in `app/config.py` (what counts as high variance, a
  large yield drop, and so on) are the tuning knobs. Change them there rather
  than in the pipeline code.
- `tests/test_pipeline.py` is a script, not pytest. Run
  `python tests/test_pipeline.py` for all ten steps, or pass a step number to
  run just one.
- The case data is synthetic. It was generated to cover the ten patterns
  evenly, five cases each.
