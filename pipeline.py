# NicheSignal v5 — pipeline.py — rewritten 2026-04-24
"""
LangGraph orchestration:
  trend_scout → content_analyzer → deep_researcher → brief_synthesizer → strict_evaluator

Conditional loop: if passed → END, if failed & revision < 2 → increment → brief_synthesizer.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph.graph import StateGraph, END
from state import NicheSignalState
from agents.trend_scout import trend_scout
from agents.content_analyzer import content_analyzer
from agents.deep_researcher import deep_researcher
from agents.rag_retriever import rag_retriever
from agents.brief_synthesizer import brief_synthesizer
from agents.strict_evaluator import strict_evaluator
from event_bus import emit_event
from rag_store import build_index

MAX_REVISIONS = 2

# Build RAG index once at module load (~1-3s, then cached in memory)
build_index()


def _increment_revision(state: NicheSignalState) -> dict:
    new_rev = state.get("revision", 0) + 1
    emit_event(f"[pipeline] Revision {new_rev}/{MAX_REVISIONS} — retrying synthesis...")
    return {
        "revision": new_rev,
        "log_events": [f"pipeline: starting revision {new_rev}"]
    }


def _route_after_evaluation(state: NicheSignalState) -> str:
    if state.get("passed_evaluation"):
        emit_event("[pipeline] ✓ Brief PASSED evaluation — done!")
        return END
    if state.get("revision", 0) >= MAX_REVISIONS:
        emit_event(f"[pipeline] ✗ Max revisions ({MAX_REVISIONS}) reached — accepting best result")
        return END
    return "increment_revision"


def build_graph() -> StateGraph:
    graph = StateGraph(NicheSignalState)

    graph.add_node("trend_scout", trend_scout)
    graph.add_node("content_analyzer", content_analyzer)
    graph.add_node("deep_researcher", deep_researcher)
    graph.add_node("rag_retriever", rag_retriever)
    graph.add_node("brief_synthesizer", brief_synthesizer)
    graph.add_node("strict_evaluator", strict_evaluator)
    graph.add_node("increment_revision", _increment_revision)

    graph.set_entry_point("trend_scout")
    graph.add_edge("trend_scout", "content_analyzer")
    graph.add_edge("content_analyzer", "deep_researcher")
    graph.add_edge("deep_researcher", "rag_retriever")
    graph.add_edge("rag_retriever", "brief_synthesizer")
    graph.add_edge("brief_synthesizer", "strict_evaluator")
    graph.add_edge("increment_revision", "brief_synthesizer")

    graph.add_conditional_edges(
        "strict_evaluator",
        _route_after_evaluation,
        {
            "increment_revision": "increment_revision",
            END: END
        }
    )

    return graph.compile()


pipeline = build_graph()


def run_pipeline(query: str) -> NicheSignalState:
    initial_state: NicheSignalState = {
        "query": query,
        "signals": [],
        "clusters": [],
        "top_signals": [],
        "full_source_content": [],
        "retrieved_briefs": [],
        "brief": None,
        "evaluation": None,
        "revision": 0,
        "passed_evaluation": False,
        "log_events": [],
    }
    return pipeline.invoke(initial_state)


def stream_pipeline(query: str):
    """Yield state updates after each node for real-time UI display."""
    initial_state: NicheSignalState = {
        "query": query,
        "signals": [],
        "clusters": [],
        "top_signals": [],
        "full_source_content": [],
        "retrieved_briefs": [],
        "brief": None,
        "evaluation": None,
        "revision": 0,
        "passed_evaluation": False,
        "log_events": [],
    }
    for event in pipeline.stream(initial_state):
        yield event