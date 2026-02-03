"""Step-by-step tests for the AI pipeline."""
import sys
import os
import json
import time

# Ensure project root is on sys.path and is cwd
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_PROJECT_ROOT)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

def step1_verify_data():
    """Step 1: Verify realistic_cases.json exists and is valid."""
    print("=" * 60)
    print("STEP 1: Verify synthetic data (realistic_cases.json)")
    print("=" * 60)
    path = "data/realistic_cases.json"
    if not os.path.exists(path):
        print(f"  FAIL: {path} does not exist")
        print("  FIX:  Run 'python synthetic_data_gen.py' first")
        return False

    with open(path, encoding="utf-8") as f:
        cases = json.load(f)

    print(f"  Loaded {len(cases)} cases")
    if len(cases) < 10:
        print(f"  FAIL: Expected at least 10 cases, got {len(cases)}")
        return False

    c = cases[0]
    print(f"  Sample case_id:  {c.get('case_id')}")
    print(f"  Sample family:   {c.get('family')}")
    print(f"  Sample severity: {c.get('severity')}")
    print(f"  Keys: {list(c.keys())}")
    print("  PASS")
    return True


def step2_rag_load_and_collection():
    """Step 2: RAG - load cases, build/load ChromaDB collection."""
    print()
    print("=" * 60)
    print("STEP 2: RAG pipeline - load cases & build ChromaDB collection")
    print("  (First run downloads BAAI/bge-small-en-v1.5 ~130MB)")
    print("=" * 60)
    try:
        from app.rag_pipeline.rag import load_cases, build_or_load_collection
        from app.config import CASES_PATH

        cases = load_cases(CASES_PATH)
        print(f"  Loaded {len(cases)} cases from config path")

        t0 = time.time()
        collection = build_or_load_collection(cases, CASES_PATH)
        elapsed = time.time() - t0
        print(f"  Collection count: {collection.count()}")
        print(f"  Collection time:  {elapsed:.1f}s (cached after first run)")
        print("  PASS")
        return cases, collection
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return None, None


def step3_rag_retrieve(cases, collection):
    """Step 3: RAG - retrieve similar cases for a sample query."""
    print()
    print("=" * 60)
    print("STEP 3: RAG retrieval - find similar cases for sample query")
    print("=" * 60)
    if cases is None:
        print("  SKIP: No cases from step 2")
        return False
    try:
        from app.rag_pipeline.rag import retrieve_similar_cases

        sample_payload = {
            "site": "Plant-A",
            "tool_group": "ETCH-CLUSTER-1",
            "process_step": "etch",
            "severity": "high",
            "anomaly_summary": "Sudden yield drop with increasing particle counts on etch tool",
            "metrics": {
                "yield_pct": 78.0,
                "affected_lot_count": 12,
                "metric_variance": 0.45,
            },
        }

        # Unfiltered retrieval
        print("  --- Unfiltered retrieval ---")
        results = retrieve_similar_cases(sample_payload, cases, collection, top_k=3)
        print(f"  Retrieved {len(results)} similar cases:")
        for i, (case, score) in enumerate(results, 1):
            print(f"    {i}. {case.get('case_id')} (family={case.get('family')}) score={score:.3f}")

        # Filtered retrieval (by process_step)
        print("  --- Filtered retrieval (process_step=etch) ---")
        filtered_results = retrieve_similar_cases(
            sample_payload, cases, collection, top_k=3,
            filters={"process_step": "etch"},
        )
        print(f"  Retrieved {len(filtered_results)} filtered cases:")
        for i, (case, score) in enumerate(filtered_results, 1):
            ctx = case.get("context", {})
            print(f"    {i}. {case.get('case_id')} (process_step={ctx.get('process_step')}) score={score:.3f}")

        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return False


def step4_backend_detection():
    """Step 4: Detect which LLM backend is available."""
    print()
    print("=" * 60)
    print("STEP 4: LLM backend detection")
    print("=" * 60)
    try:
        from app.rag_pipeline.llm import detect_backend
        backend = detect_backend()
        labels = {
            "huggingface": "HuggingFace Inference API",
            "ollama": "Ollama (local)",
            "placeholder": "No LLM (heuristic fallback)",
        }
        print(f"  Detected backend: {backend} ({labels.get(backend, '?')})")
        print("  PASS")
        return backend
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        return None


def step5_investigation_assessment(cases, collection):
    """Step 5: Test rule-based investigation assessment."""
    print()
    print("=" * 60)
    print("STEP 5: Rule-based investigation assessment")
    print("=" * 60)
    try:
        from app.rag_pipeline.triage import assess_investigation

        sample_payload = {
            "site": "Plant-A",
            "tool_group": "ETCH-CLUSTER-1",
            "process_step": "etch",
            "severity": "high",
            "anomaly_summary": "Sudden yield drop with increasing particle counts",
            "metrics": {
                "yield_pct": 78.0,
                "affected_lot_count": 12,
                "metric_variance": 0.45,
            },
        }

        # Build similar cases list like ai_engine does (list of tuples)
        from app.rag_pipeline.rag import retrieve_similar_cases
        similar = []
        if cases is not None and collection is not None:
            similar = retrieve_similar_cases(sample_payload, cases, collection, top_k=3)

        assessment = assess_investigation(sample_payload, similar)
        print(f"  Pattern:    {assessment.get('pattern')}")
        print(f"  Priority:   {assessment.get('priority')}")
        print(f"  Confidence: {assessment.get('confidence')}")
        print(f"  Approach:   {assessment.get('diagnostic_approach', '')[:80]}...")
        print(f"  Reasoning:  {assessment.get('reasoning', '')[:80]}...")
        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return False


def step6_full_pipeline():
    """Step 6: Full ai_engine.build_ai_response end-to-end."""
    print()
    print("=" * 60)
    print("STEP 6: Full pipeline - build_ai_response()")
    print("  (This is what runs when user clicks Submit)")
    print("=" * 60)
    try:
        from app.rag_pipeline.engine import build_ai_response

        sample_payload = {
            "site": "Plant-A",
            "tool_group": "ETCH-CLUSTER-1",
            "process_step": "etch",
            "severity": "high",
            "timestamp": "2025-01-30T10:00:00",
            "anomaly_summary": "Sudden yield drop with increasing particle counts on etch tool",
            "metrics": {
                "yield_pct": 78.0,
                "affected_lot_count": 12,
                "time_window_hours": 24,
                "metric_variance": 0.45,
                "change_magnitude": -8.5,
                "measurement_confidence": 0.65,
                "rework_rate": 6.1,
            },
        }

        t0 = time.time()
        response = build_ai_response(sample_payload)
        elapsed = time.time() - t0

        print(f"  Response time: {elapsed:.1f}s")
        print(f"  Keys: {list(response.keys())}")

        # Assessment
        a = response.get("assessment", {})
        print(f"  Assessment: priority={a.get('priority')}, pattern={a.get('pattern')}, confidence={a.get('confidence')}")
        print(f"  Assessment source: {a.get('source')}")

        # Similar cases
        sc = response.get("similar_cases", [])
        print(f"  Similar cases: {len(sc)}")

        # Next checks
        nc = response.get("next_checks", [])
        print(f"  Next checks: {len(nc)}")
        if nc:
            print(f"    First: {nc[0].get('category')}: {nc[0].get('check', '')[:60]}...")

        # Narrative
        narr = response.get("narrative", "")
        print(f"  Narrative length: {len(narr)} chars")
        if narr:
            print(f"    Preview: {narr[:100]}...")

        # Escalation
        esc = response.get("escalation_summary", "")
        print(f"  Escalation summary: {len(esc)} chars")

        # Meta
        meta = response.get("meta", {})
        print(f"  Backend: {meta.get('backend')}")
        print(f"  Model:   {meta.get('model', 'N/A')}")
        print(f"  RAG cases retrieved: {meta.get('rag_cases_retrieved')}")

        # Timings
        timings = meta.get("timings", {})
        print(f"  Timings: {timings}")
        if not timings:
            print("  WARN: No timings in response meta")
        else:
            print(f"    RAG: {timings.get('rag_retrieval_ms', '?')}ms")
            print(f"    LLM: {timings.get('llm_generation_ms', '?')}ms")
            print(f"    Total: {timings.get('total_ms', '?')}ms")

        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return False


def step7_pydantic_models():
    """Step 7: Pydantic model validation."""
    print()
    print("=" * 60)
    print("STEP 7: Pydantic model validation")
    print("=" * 60)
    try:
        from pydantic import ValidationError
        from app.core.models import (
            LLMInvestigationResponse,
            LLMAssessmentResponse,
            PipelineTimings,
            NLPExtractionResponse,
        )

        # Valid investigation response
        valid_investigation = {
            "narrative": "Test narrative text.",
            "next_checks": [
                {"category": "Equipment", "check": "Check tool X", "why": "Because Y"},
                {"category": "Process", "check": "Review step Z", "why": "Because W"},
            ],
            "escalation_summary": "Summary of escalation.",
        }
        resp = LLMInvestigationResponse(**valid_investigation)
        print(f"  Valid investigation: OK (narrative={len(resp.narrative)} chars, checks={len(resp.next_checks)})")

        # Valid assessment response
        valid_assessment = {
            "pattern": "Gradual Drift",
            "priority": "High",
            "confidence": "Medium",
            "diagnostic_approach": "Check the trend data first.",
            "reasoning": "Signals suggest gradual degradation.",
        }
        assessment = LLMAssessmentResponse(**valid_assessment)
        print(f"  Valid assessment: OK (pattern={assessment.pattern}, priority={assessment.priority.value})")

        # Invalid: bad priority value
        bad_assessment = {**valid_assessment, "priority": "EXTREME"}
        try:
            LLMAssessmentResponse(**bad_assessment)
            print("  FAIL: Should have rejected invalid priority 'EXTREME'")
            return False
        except ValidationError:
            print("  Invalid priority rejected: OK")

        # Invalid: missing required field
        incomplete = {"narrative": "text only"}
        try:
            LLMInvestigationResponse(**incomplete)
            print("  FAIL: Should have rejected incomplete investigation response")
            return False
        except ValidationError:
            print("  Incomplete response rejected: OK")

        # PipelineTimings defaults
        timings = PipelineTimings()
        assert timings.rag_retrieval_ms == 0
        assert timings.total_ms == 0
        print("  PipelineTimings defaults: OK")

        # --- NLPExtractionResponse tests ---
        print()
        print("  --- NLPExtractionResponse ---")

        # Valid NLP extraction with all fields
        valid_nlp = {
            "site": "Plant-A",
            "tool_group": "ETCH-CLUSTER-1",
            "process_step": "etch",
            "severity": "high",
            "anomaly_summary": "Yield dropped suddenly",
            "yield_pct": 78.0,
            "metric_variance": 0.45,
            "change_magnitude": -8.5,
            "measurement_confidence": 0.65,
            "affected_lot_count": 12,
            "rework_rate": 6.1,
            "time_window_hours": 24,
        }
        nlp_resp = NLPExtractionResponse(**valid_nlp)
        print(f"  Valid NLP extraction: OK (site={nlp_resp.site}, yield={nlp_resp.yield_pct})")

        # Case-insensitive normalization
        case_insensitive_nlp = {
            "site": "plant-a",
            "tool_group": "etch-cluster-1",
            "process_step": "ETCH",
            "severity": "HIGH",
        }
        nlp_case = NLPExtractionResponse(**case_insensitive_nlp)
        assert nlp_case.site == "Plant-A", f"Expected 'Plant-A', got '{nlp_case.site}'"
        assert nlp_case.tool_group == "ETCH-CLUSTER-1", f"Expected 'ETCH-CLUSTER-1', got '{nlp_case.tool_group}'"
        assert nlp_case.process_step == "etch", f"Expected 'etch', got '{nlp_case.process_step}'"
        assert nlp_case.severity == "high", f"Expected 'high', got '{nlp_case.severity}'"
        print("  Case-insensitive normalization: OK")

        # Invalid config values become None
        invalid_nlp = {
            "site": "NonExistentPlant",
            "tool_group": "FAKE-TOOL",
            "process_step": "fake_step",
            "severity": "extreme",
        }
        nlp_invalid = NLPExtractionResponse(**invalid_nlp)
        assert nlp_invalid.site is None, f"Expected None for invalid site, got '{nlp_invalid.site}'"
        assert nlp_invalid.tool_group is None, f"Expected None for invalid tool_group, got '{nlp_invalid.tool_group}'"
        assert nlp_invalid.process_step is None, f"Expected None for invalid process_step, got '{nlp_invalid.process_step}'"
        assert nlp_invalid.severity is None, f"Expected None for invalid severity, got '{nlp_invalid.severity}'"
        print("  Invalid config values -> None: OK")

        # All-None NLP (empty extraction)
        empty_nlp = NLPExtractionResponse()
        assert empty_nlp.site is None
        assert empty_nlp.yield_pct is None
        print("  Empty NLP extraction: OK")

        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return False


def step8_response_caching():
    """Step 8: Response caching — same payload returns cached result."""
    print()
    print("=" * 60)
    print("STEP 8: Response caching")
    print("=" * 60)
    try:
        from app.rag_pipeline.engine import build_ai_response, _response_cache

        sample_payload = {
            "site": "Plant-B",
            "tool_group": "LITHO-LINE-1",
            "process_step": "lithography",
            "severity": "medium",
            "timestamp": "2025-02-01T12:00:00",
            "anomaly_summary": "Cache test - overlay drift detected on litho scanner",
            "metrics": {
                "yield_pct": 88.0,
                "affected_lot_count": 4,
                "time_window_hours": 36,
                "metric_variance": 0.22,
                "change_magnitude": -3.1,
                "measurement_confidence": 0.72,
                "rework_rate": 3.5,
            },
        }

        # First call — should NOT be cached
        response1 = build_ai_response(sample_payload)
        is_cached_1 = response1.get("meta", {}).get("from_cache", False)
        print(f"  First call cached: {is_cached_1} (expected: False)")

        # Second call — should be cached
        response2 = build_ai_response(sample_payload)
        is_cached_2 = response2.get("meta", {}).get("from_cache", False)
        print(f"  Second call cached: {is_cached_2} (expected: True)")

        if is_cached_1:
            print("  FAIL: First call should not be cached")
            return False
        if not is_cached_2:
            print("  FAIL: Second call should be cached")
            return False

        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return False


def step9_timing_metadata():
    """Step 9: Verify response contains timing fields."""
    print()
    print("=" * 60)
    print("STEP 9: Timing metadata in response")
    print("=" * 60)
    try:
        from app.rag_pipeline.engine import build_ai_response

        sample_payload = {
            "site": "Plant-C",
            "tool_group": "DEP-STACK-1",
            "process_step": "deposition",
            "severity": "low",
            "timestamp": "2025-02-01T14:00:00",
            "anomaly_summary": "Timing test - minor thickness variation on dep tool",
            "metrics": {
                "yield_pct": 94.0,
                "affected_lot_count": 2,
                "time_window_hours": 12,
                "metric_variance": 0.08,
                "change_magnitude": -1.2,
                "measurement_confidence": 0.91,
                "rework_rate": 1.0,
            },
        }

        response = build_ai_response(sample_payload)
        meta = response.get("meta", {})
        timings = meta.get("timings", {})

        required_keys = ["rag_retrieval_ms", "llm_generation_ms", "total_ms"]
        missing = [k for k in required_keys if k not in timings]
        if missing:
            print(f"  FAIL: Missing timing keys: {missing}")
            return False

        for key in required_keys:
            val = timings[key]
            if not isinstance(val, int) or val < 0:
                print(f"  FAIL: {key}={val} is not a valid non-negative integer")
                return False
            print(f"  {key}: {val}ms")

        # total_ms should be >= rag_retrieval_ms
        if timings["total_ms"] < timings["rag_retrieval_ms"]:
            print("  FAIL: total_ms should be >= rag_retrieval_ms")
            return False

        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return False


def step10_nlp_extraction():
    """Step 10: NLP extraction end-to-end (skip if no LLM backend)."""
    print()
    print("=" * 60)
    print("STEP 10: NLP extraction end-to-end")
    print("=" * 60)
    try:
        from app.rag_pipeline.llm import detect_backend, extract_fields_from_text

        backend = detect_backend()
        if backend == "placeholder":
            print("  SKIP: No LLM backend available (NLP extraction requires an LLM)")
            return True

        sample_text = (
            "Yield dropped to 78% on ETCH-CLUSTER-1 at Plant-A, "
            "12 lots affected over 24 hours, high severity etch issue. "
            "Variance is 0.45, change magnitude -8.5, measurement confidence 0.65, "
            "rework rate 6.1%."
        )

        result = extract_fields_from_text(sample_text, backend)
        if result is None:
            print("  FAIL: extract_fields_from_text returned None")
            return False

        print(f"  Extracted fields:")
        for k, v in result.items():
            if v is not None:
                print(f"    {k}: {v}")

        # Basic sanity checks
        if result.get("yield_pct") is not None:
            print(f"  yield_pct extracted: {result['yield_pct']}")
        if result.get("site") is not None:
            print(f"  site extracted: {result['site']}")

        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run specific step or all
    step = sys.argv[1] if len(sys.argv) > 1 else "all"

    if step in ("1", "all"):
        ok = step1_verify_data()
        if not ok and step == "all":
            print("\nStopping: Step 1 failed. Fix data first.")
            sys.exit(1)

    if step in ("2", "all"):
        cases, collection = step2_rag_load_and_collection()

    if step in ("3", "all"):
        if step == "3":
            cases, collection = step2_rag_load_and_collection()
        step3_rag_retrieve(cases, collection)

    if step in ("4", "all"):
        step4_backend_detection()

    if step in ("5", "all"):
        if step == "5":
            cases, collection = step2_rag_load_and_collection()
        step5_investigation_assessment(cases, collection)

    if step in ("6", "all"):
        step6_full_pipeline()

    if step in ("7", "all"):
        step7_pydantic_models()

    if step in ("8", "all"):
        step8_response_caching()

    if step in ("9", "all"):
        step9_timing_metadata()

    if step in ("10", "all"):
        step10_nlp_extraction()

    if step == "all":
        print()
        print("=" * 60)
        print("ALL STEPS COMPLETE")
        print("=" * 60)
