"""
RAG pipeline: ChromaDB-backed retrieval over historical investigation cases.
Uses sentence-transformers with BAAI/bge-small-en-v1.5 via ChromaDB's
SentenceTransformerEmbeddingFunction. Supports metadata filtering for
pre-filtering by process_step, site, tool_group, etc.
"""
from __future__ import annotations

import json
import hashlib
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.config import CHROMA_PERSIST_DIR

MODEL_NAME = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME = "investigation_cases"

_chroma_client: Optional[chromadb.ClientAPI] = None
_embedding_fn: Optional[SentenceTransformerEmbeddingFunction] = None
_collection: Optional[chromadb.Collection] = None


def _get_embedding_fn() -> SentenceTransformerEmbeddingFunction:
    """Lazy-load the SentenceTransformerEmbeddingFunction (cached after first call)."""
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    return _embedding_fn


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


def _extract_case_metadata(case: Dict[str, Any]) -> Dict[str, str]:
    """Extract filterable metadata fields from a case record."""
    ctx = case.get("context", {})
    signals = case.get("signals", {})
    return {
        "case_id": case.get("case_id", ""),
        "process_step": ctx.get("process_step", ""),
        "site": ctx.get("site", ""),
        "tool_group": ctx.get("tool_group", ""),
        "yield_severity": signals.get("yield_severity", ""),
        "family": case.get("family", ""),
        "_case_json": json.dumps(case),
    }


def build_or_load_collection(
    cases: List[Dict[str, Any]],
    cases_path: str,
    persist_dir: Optional[str] = None,
) -> chromadb.Collection:
    """
    Build a ChromaDB collection from cases, or load from persistent storage
    if the cases file hasn't changed. Replaces build_or_load_embeddings().

    Returns a chromadb.Collection ready for querying.
    """
    global _chroma_client, _collection

    if persist_dir is None:
        persist_dir = CHROMA_PERSIST_DIR

    current_hash = _compute_file_hash(cases_path)

    # Initialize persistent client
    _chroma_client = chromadb.PersistentClient(path=persist_dir)
    ef = _get_embedding_fn()

    # Check if collection exists with matching hash and count
    existing_names = [c.name for c in _chroma_client.list_collections()]
    needs_rebuild = True

    if COLLECTION_NAME in existing_names:
        collection = _chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
        )
        # Check hash via collection metadata and count
        coll_meta = collection.metadata or {}
        if (
            coll_meta.get("cases_hash") == current_hash
            and collection.count() == len(cases)
        ):
            needs_rebuild = False
            _collection = collection
            return collection

    if needs_rebuild:
        # Delete stale collection if it exists
        if COLLECTION_NAME in existing_names:
            _chroma_client.delete_collection(name=COLLECTION_NAME)

        # Create new collection with cosine distance
        collection = _chroma_client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
            metadata={
                "hnsw:space": "cosine",
                "cases_hash": current_hash,
            },
        )

        # Add all cases in a single batch
        documents = [case_to_text(c) for c in cases]
        metadatas = [_extract_case_metadata(c) for c in cases]
        ids = [f"case_{i}" for i in range(len(cases))]

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        _collection = collection
        return collection


def _build_where_clause(filters: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Convert a dict of field->value filters to ChromaDB where format.
    Skips empty/placeholder values. Returns None if no valid filters.
    """
    conditions = []
    for field, value in filters.items():
        if value and not value.startswith("—"):
            conditions.append({field: {"$eq": value}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def retrieve_similar_cases(
    payload: Dict[str, Any],
    cases: List[Dict[str, Any]],
    collection: chromadb.Collection,
    top_k: int = 3,
    filters: Optional[Dict[str, str]] = None,
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Query ChromaDB collection for similar cases using the user payload.
    Optionally applies metadata filters for pre-filtering.

    Returns top-k cases with their similarity scores (descending),
    as List[Tuple[case_dict, similarity_score]].
    """
    query_text = payload_to_query_text(payload)

    query_params: Dict[str, Any] = {
        "query_texts": [query_text],
        "n_results": top_k,
    }

    if filters:
        where_clause = _build_where_clause(filters)
        if where_clause:
            query_params["where"] = where_clause

    try:
        results = collection.query(**query_params)
    except Exception:
        # If filtered query fails (e.g. no matching docs), retry without filters
        query_params.pop("where", None)
        results = collection.query(**query_params)

    output: List[Tuple[Dict[str, Any], float]] = []

    if results and results["metadatas"] and results["distances"]:
        for metadata, distance in zip(results["metadatas"][0], results["distances"][0]):
            # ChromaDB cosine distance = 1 - similarity
            similarity = 1.0 - distance
            case_dict = json.loads(metadata["_case_json"])
            output.append((case_dict, similarity))

    return output
