# NicheSignal v5 — state.py — rewritten 2026-04-24
from typing import TypedDict, Annotated, Optional
import operator


class NicheSignalState(TypedDict):
    query: str
    signals: list[dict]
    clusters: list[dict]
    top_signals: list[dict]
    full_source_content: list[dict]
    retrieved_briefs: list[dict]   # RAG: similar past briefs (from rag_retriever)
    brief: Optional[dict]
    evaluation: Optional[dict]
    revision: int
    passed_evaluation: bool
    log_events: Annotated[list[str], operator.add]