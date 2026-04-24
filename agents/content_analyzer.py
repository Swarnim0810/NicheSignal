# NicheSignal v5 — content_analyzer.py — rewritten 2026-04-24
"""
Clusters signals using semantic embeddings (all-MiniLM-L6-v2).
Cosine similarity threshold: 0.6.
Source diversity denominator: 6 (HN, GitHub, SO, Dev.to, Lobsters, Google Trends).
"""

import numpy as np
from state import NicheSignalState
from event_bus import emit_event

_model = None
_CLUSTER_THRESHOLD = 0.6
_SOURCE_COUNT = 6


def _get_model():
    """Lazy-load the sentence-transformer model (cached after first call)."""
    global _model
    if _model is None:
        emit_event("[content_analyzer] Loading embedding model...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        emit_event("[content_analyzer] ✓ Embedding model loaded")
    return _model


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _cluster_signals(signals: list[dict], embeddings: np.ndarray) -> list[dict]:
    """Greedy clustering using cosine similarity on embeddings."""
    clusters: list[dict] = []

    for i, signal in enumerate(signals):
        placed = False
        for cluster in clusters:
            rep_idx = cluster["_rep_idx"]
            sim = _cosine_sim(embeddings[i], embeddings[rep_idx])
            if sim >= _CLUSTER_THRESHOLD:
                cluster["signals"].append(signal)
                cluster["total_score"] += signal["score"]
                cluster["sources"].add(signal["source"].split("/")[0])
                placed = True
                break
        if not placed:
            clusters.append({
                "_rep_idx": i,
                "representative": signal,
                "signals": [signal],
                "total_score": signal["score"],
                "sources": {signal["source"].split("/")[0]},
            })

    # Compute momentum scores and human-readable fields
    for cluster in clusters:
        src_list = list(cluster["sources"])
        sig_count = len(cluster["signals"])
        cluster["sources"] = src_list
        cluster["signal_count"] = sig_count
        cluster["sources_found_in"] = f"{len(src_list)}/{_SOURCE_COUNT} sources"
        cluster["top_source_examples"] = [
            s["title"][:80] for s in sorted(cluster["signals"], key=lambda s: s["score"], reverse=True)[:3]
        ]
        cluster["momentum_score"] = round(
            cluster["total_score"] * 0.5
            + len(src_list) / _SOURCE_COUNT * 0.3
            + min(sig_count / 5, 1.0) * 0.2,
            3
        )
        del cluster["_rep_idx"]

    clusters.sort(key=lambda c: c["momentum_score"], reverse=True)
    return clusters


def content_analyzer(state: NicheSignalState) -> dict:
    signals = state.get("signals", [])
    emit_event(f"[content_analyzer] Clustering {len(signals)} signals...")

    if not signals:
        emit_event("[content_analyzer] ⚠ No signals to cluster")
        return {
            "clusters": [],
            "top_signals": [],
            "log_events": ["content_analyzer: no signals to cluster"]
        }

    # Compute embeddings
    model = _get_model()
    titles = [s.get("title", "") for s in signals]
    embeddings = model.encode(titles, show_progress_bar=False)

    clusters = _cluster_signals(signals, embeddings)
    top_clusters = clusters[:5]

    top_signals: list[dict] = []
    for cluster in top_clusters:
        best = max(cluster["signals"], key=lambda s: s["score"])
        top_signals.append(best)
        emit_event(
            f"[content_analyzer] Cluster formed — {cluster['signal_count']} signals — "
            f"\"{cluster['representative']['title'][:50]}\" — momentum {cluster['momentum_score']:.2f}"
        )

    emit_event(f"[content_analyzer] ✓ {len(clusters)} clusters, {len(top_signals)} top signals")

    return {
        "clusters": clusters,
        "top_signals": top_signals,
        "log_events": [f"content_analyzer: {len(clusters)} clusters, {len(top_signals)} top"]
    }