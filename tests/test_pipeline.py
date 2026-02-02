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


def step2_rag_load_and_embed():
    """Step 2: RAG - load cases, build embeddings."""
    print()
    print("=" * 60)
    print("STEP 2: RAG pipeline - load cases & build embeddings")
    print("  (First run downloads BAAI/bge-small-en-v1.5 ~130MB)")
    print("=" * 60)
    try:
        from app.rag_pipeline.rag import load_cases, build_or_load_embeddings
        from app.config import CASES_PATH

        cases = load_cases(CASES_PATH)
        print(f"  Loaded {len(cases)} cases from config path")

        t0 = time.time()
        embeddings = build_or_load_embeddings(cases, CASES_PATH)
        elapsed = time.time() - t0
        print(f"  Embeddings shape: {embeddings.shape}")
        print(f"  Embedding time:   {elapsed:.1f}s (cached after first run)")
        print("  PASS")
        return cases, embeddings
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        return None, None


def step3_rag_retrieve(cases, embeddings):
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

        results = retrieve_similar_cases(sample_payload, cases, embeddings, top_k=3)
        print(f"  Retrieved {len(results)} similar cases:")
        for i, (case, score) in enumerate(results, 1):
            print(f"    {i}. {case.get('case_id')} (family={case.get('family')}) score={score:.3f}")
        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
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


def step5_investigation_assessment(cases, embeddings):
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
        if cases is not None and embeddings is not None:
            similar = retrieve_similar_cases(sample_payload, cases, embeddings, top_k=3)

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
        cases, embeddings = step2_rag_load_and_embed()

    if step in ("3", "all"):
        if step == "3":
            cases, embeddings = step2_rag_load_and_embed()
        step3_rag_retrieve(cases, embeddings)

    if step in ("4", "all"):
        step4_backend_detection()

    if step in ("5", "all"):
        if step == "5":
            cases, embeddings = step2_rag_load_and_embed()
        step5_investigation_assessment(cases, embeddings)

    if step in ("6", "all"):
        step6_full_pipeline()

    if step == "all":
        print()
        print("=" * 60)
        print("ALL STEPS COMPLETE")
        print("=" * 60)
