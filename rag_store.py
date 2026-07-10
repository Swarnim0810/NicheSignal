# NicheSignal v5 — rag_store.py
"""
Singleton vector store over query_history.json.
- Uses all-MiniLM-L6-v2 (same model as content_analyzer) for embeddings.
- Only indexes entries where passed=True to avoid retrieving low-quality briefs.
- build_index() runs once at pipeline startup (~1-3s for ~436 entries).
- retrieve() is pure numpy — no LLM calls, <50ms latency.
"""

import json
import numpy as np
from pathlib import Path
from event_bus import emit_event

_model = None
_index: list[dict] = []   # list of {query, angle, title, embedding}


def _get_model():
    """Lazy-load all-MiniLM-L6-v2 (singleton pattern, same as content_analyzer)."""
    global _model
    if _model is None:
        emit_event("[rag_store] Loading embedding model for RAG index...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        emit_event("[rag_store] ✓ Embedding model ready")
    return _model


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def build_index(history_path: str = "query_history.json") -> None:
    """
    Build the in-memory vector index from query_history.json.
    Only indexes entries with passed=True.
    Call once at pipeline startup.
    """
    global _index
    path = Path(history_path)
    if not path.exists():
        emit_event(f"[rag_store] ⚠ No history file found at {history_path} — RAG disabled")
        _index = []
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        emit_event(f"[rag_store] ⚠ Failed to read history file — {e}")
        _index = []
        return

    # Only index passed briefs with a valid content_angle
    valid = [
        entry for entry in data
        if entry.get("passed") is True
        and isinstance(entry.get("brief"), dict)
        and entry["brief"].get("content_angle")
    ]

    if not valid:
        emit_event("[rag_store] ⚠ No valid passed entries found — RAG disabled")
        _index = []
        return

    model = _get_model()
    queries = [entry["query"] for entry in valid]
    embeddings = model.encode(queries, show_progress_bar=False)

    _index = [
        {
            "query": valid[i]["query"],
            # Only keep 3 compressed fields per entry — ~40-60 tokens total
            "content_angle": valid[i]["brief"].get("content_angle", ""),
            "suggested_title": valid[i]["brief"].get("suggested_title", ""),
            "gap_summary": valid[i]["brief"].get("gap_summary", ""),
            "embedding": embeddings[i],
        }
        for i in range(len(valid))
    ]

    emit_event(f"[rag_store] ✓ Index built — {len(_index)} past briefs indexed")


def retrieve(query: str, top_k: int = 3, min_similarity: float = 0.35) -> list[dict]:
    """
    Return up to top_k most semantically similar past briefs.
    Only returns results above min_similarity to avoid irrelevant noise.
    Never returns the current query if it's already in the index.
    Each result contains: query, content_angle, suggested_title, gap_summary, similarity.
    """
    if not _index:
        return []

    model = _get_model()
    q_emb = model.encode([query])[0]

    scored = []
    for item in _index:
        # Skip exact matches (same query re-run)
        if item["query"].strip().lower() == query.strip().lower():
            continue
        sim = _cosine_sim(q_emb, item["embedding"])
        if sim >= min_similarity:
            scored.append((sim, item))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for sim, item in scored[:top_k]:
        results.append({
            "query": item["query"],
            "content_angle": item["content_angle"],
            "suggested_title": item["suggested_title"],
            "gap_summary": item["gap_summary"],
            "similarity": round(sim, 3),
        })

    return results


def index_size() -> int:
    """Return the number of entries currently in the index."""
    return len(_index)
