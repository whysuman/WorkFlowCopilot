"""
RAG pipeline: embedding-based retrieval over historical investigation cases.
Uses sentence-transformers with BAAI/bge-small-en-v1.5 for local embeddings.
Pre-computes and caches embeddings to disk as .npy files.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

_model = None

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDINGS_DIR = Path(__file__).parent / "data"
EMBEDDINGS_FILE = EMBEDDINGS_DIR / "case_embeddings.npy"
EMBEDDINGS_HASH_FILE = EMBEDDINGS_DIR / "case_embeddings_hash.txt"


def _get_model():
    """Lazy-load the sentence-transformer model (cached after first call)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def case_to_text(case: Dict[str, Any]) -> str:
    """
    Convert a case record to a textual representation for embedding.
    Combines context, metrics summary, signals, and resolution.
    """
    ctx = case.get("context", {})
    metrics = case.get("metrics", {})
    signals = case.get("signals", {})

    parts = [
        f"Family: {case.get('family', '')}",
        f"Site: {ctx.get('site', '')}, Tool group: {ctx.get('tool_group', '')}, "
        f"Process step: {ctx.get('process_step', '')}",
        f"Yield: {metrics.get('yield_pct', '')}%, Variance: {metrics.get('metric_variance', '')}, "
        f"Change magnitude: {metrics.get('change_magnitude', '')}, "
        f"Measurement confidence: {metrics.get('measurement_confidence', '')}",
        f"Affected lots: {metrics.get('affected_lot_count', '')}, "
        f"Rework rate: {metrics.get('rework_rate', '')}%, "
        f"Time window: {metrics.get('time_window_hours', '')}h",
        f"Yield severity: {signals.get('yield_severity', '')}, "
        f"Variance: {signals.get('variance_bucket', '')}, "
        f"Change direction: {signals.get('change_dir', '')}",
        f"Matched signals: {case.get('matched_signals_template', '')}",
        f"Resolution: {case.get('resolution_summary', '')}",
    ]
    return " | ".join(parts)


def payload_to_query_text(payload: Dict[str, Any]) -> str:
    """
    Convert the user's investigation payload into a query string for embedding.
    Mirrors the structure of case_to_text for best similarity matching.
    """
    metrics = payload.get("metrics", {})
    parts = [
        f"Site: {payload.get('site', '')}, Tool group: {payload.get('tool_group', '')}, "
        f"Process step: {payload.get('process_step', '')}",
        f"Severity: {payload.get('severity', '')}",
        f"Summary: {payload.get('anomaly_summary', '')}",
    ]
    metric_fields = [
        ("yield_pct", "Yield", "%"),
        ("metric_variance", "Variance", ""),
        ("change_magnitude", "Change magnitude", ""),
        ("measurement_confidence", "Measurement confidence", ""),
        ("affected_lot_count", "Affected lots", ""),
        ("rework_rate", "Rework rate", "%"),
        ("time_window_hours", "Time window", "h"),
    ]
    for key, label, suffix in metric_fields:
        val = metrics.get(key)
        if val is not None:
            parts.append(f"{label}: {val}{suffix}")
    return " | ".join(parts)


def _compute_file_hash(filepath: str) -> str:
    """Compute MD5 hash of the cases file to detect changes."""
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_cases(cases_path: str) -> List[Dict[str, Any]]:
    """Load cases from JSON file."""
    with open(cases_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_or_load_embeddings(
    cases: List[Dict[str, Any]],
    cases_path: str,
) -> np.ndarray:
    """
    Build embeddings for all cases, or load from cache if cases haven't changed.
    Returns numpy array of shape (n_cases, embedding_dim).
    """
    current_hash = _compute_file_hash(cases_path)

    if EMBEDDINGS_FILE.exists() and EMBEDDINGS_HASH_FILE.exists():
        cached_hash = EMBEDDINGS_HASH_FILE.read_text().strip()
        if cached_hash == current_hash:
            return np.load(str(EMBEDDINGS_FILE))

    model = _get_model()
    texts = [case_to_text(c) for c in cases]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    np.save(str(EMBEDDINGS_FILE), embeddings)
    EMBEDDINGS_HASH_FILE.write_text(current_hash)

    return embeddings


def retrieve_similar_cases(
    payload: Dict[str, Any],
    cases: List[Dict[str, Any]],
    case_embeddings: np.ndarray,
    top_k: int = 3,
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Embed the user payload, compute cosine similarity against all cases,
    return top-k cases with their similarity scores (descending).
    """
    model = _get_model()
    query_text = payload_to_query_text(payload)
    query_embedding = model.encode([query_text], convert_to_numpy=True)[0]

    # Cosine similarity
    norms_cases = np.linalg.norm(case_embeddings, axis=1)
    norm_query = np.linalg.norm(query_embedding)

    # Avoid division by zero
    norms_cases = np.maximum(norms_cases, 1e-10)
    norm_query = max(norm_query, 1e-10)

    similarities = (case_embeddings @ query_embedding) / (norms_cases * norm_query)

    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append((cases[int(idx)], float(similarities[idx])))
    return results
