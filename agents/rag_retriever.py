# NicheSignal v5 — rag_retriever.py
"""
LangGraph node: retrieves semantically similar past briefs from rag_store.
No LLM calls — pure embedding similarity search.
Populates state["retrieved_briefs"] with top-k compressed past brief entries.
Token cost of this node: 0 (no API call).
"""

from state import NicheSignalState
from event_bus import emit_event
from rag_store import retrieve, index_size


def rag_retriever(state: NicheSignalState) -> dict:
    query = state["query"]
    n_indexed = index_size()

    emit_event(f"[rag_retriever] Searching {n_indexed} indexed past briefs for: \"{query}\"")

    if n_indexed == 0:
        emit_event("[rag_retriever] ⚠ RAG index is empty — skipping retrieval")
        return {
            "retrieved_briefs": [],
            "log_events": ["rag_retriever: index empty, skipped"]
        }

    results = retrieve(query, top_k=3, min_similarity=0.35)

    if results:
        for r in results:
            emit_event(
                f"[rag_retriever] ↳ sim={r['similarity']:.2f} | \"{r['query']}\" → \"{r['suggested_title'][:60]}\""
            )
        emit_event(f"[rag_retriever] ✓ Retrieved {len(results)} relevant past brief(s)")
    else:
        emit_event("[rag_retriever] ✓ No similar past briefs above threshold — proceeding fresh")

    return {
        "retrieved_briefs": results,
        "log_events": [f"rag_retriever: {len(results)} past briefs retrieved (index_size={n_indexed})"]
    }
