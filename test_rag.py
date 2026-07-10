"""
RAG Integration Test Suite — NicheSignal v3
Tests every component of the RAG implementation end-to-end.
"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import numpy as np

print("=" * 70)
print("  NicheSignal RAG Integration Test Suite")
print("=" * 70)

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name} — {detail}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[1/6] State Schema")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from state import NicheSignalState
annotations = NicheSignalState.__annotations__
test("retrieved_briefs field exists", "retrieved_briefs" in annotations)
test("retrieved_briefs type is list[dict]", annotations.get("retrieved_briefs") == list[dict])
test("all original fields preserved", all(
    f in annotations for f in ["query", "signals", "clusters", "top_signals",
                                "full_source_content", "brief", "evaluation",
                                "revision", "passed_evaluation", "log_events"]
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[2/6] RAG Store")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import rag_store

# Test build_index with actual query_history.json
rag_store.build_index("query_history.json")
idx_size = rag_store.index_size()
test("Index built from query_history.json", idx_size > 0, f"got {idx_size}")

# Verify index only contains passed entries
history = json.loads(open("query_history.json", encoding="utf-8").read())
passed_count = sum(1 for e in history if e.get("passed") is True and isinstance(e.get("brief"), dict) and e["brief"].get("content_angle"))
test("Index size matches passed entries", idx_size == passed_count, f"index={idx_size}, passed={passed_count}")

# Test retrieval with a query that should match
results = rag_store.retrieve("robotic arm", top_k=3)
test("Retrieve returns results for 'robotic arm'", len(results) > 0, f"got {len(results)}")
test("Results have required fields", all(
    "query" in r and "content_angle" in r and "suggested_title" in r and "similarity" in r
    for r in results
), f"keys: {results[0].keys() if results else 'empty'}")
test("Similarity scores are floats in [0,1]", all(
    isinstance(r["similarity"], float) and 0 <= r["similarity"] <= 1
    for r in results
))

# Test exact-match exclusion (should not return itself)
exact_results = rag_store.retrieve("robotic arm", top_k=10)
test("Exact query excluded from results", all(
    r["query"].strip().lower() != "robotic arm" for r in exact_results
))

# Test with gibberish query — should return empty or low similarity
gibberish = rag_store.retrieve("xyzzy123foobarbaz", top_k=3, min_similarity=0.8)
test("Gibberish query returns no high-sim results", len(gibberish) == 0)

# Test graceful fallback with missing file
rag_store.build_index("nonexistent_file.json")
test("Missing file → empty index gracefully", rag_store.index_size() == 0)

# Rebuild for remaining tests
rag_store.build_index("query_history.json")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[3/6] RAG Retriever Agent")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from agents.rag_retriever import rag_retriever

# Simulate a state
mock_state = {
    "query": "AI code generation",
    "signals": [], "clusters": [], "top_signals": [],
    "full_source_content": [], "retrieved_briefs": [],
    "brief": None, "evaluation": None,
    "revision": 0, "passed_evaluation": False, "log_events": [],
}

result = rag_retriever(mock_state)
test("Returns dict with 'retrieved_briefs'", "retrieved_briefs" in result)
test("Returns dict with 'log_events'", "log_events" in result)
test("retrieved_briefs is a list", isinstance(result["retrieved_briefs"], list))
test("log_events is a list", isinstance(result["log_events"], list))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[4/6] Brief Synthesizer RAG Integration")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from agents.brief_synthesizer import _format_rag_context, _build_prompt

# Test empty context
test("Empty RAG → empty string", _format_rag_context([]) == "")

# Test with sample briefs
sample_briefs = [
    {"query": "rust async", "content_angle": "Tokio internals", "suggested_title": "Why Tokio Wins", "similarity": 0.8},
    {"query": "python async", "content_angle": "asyncio pitfalls", "suggested_title": "asyncio Hidden Costs", "similarity": 0.6},
]
rag_block = _format_rag_context(sample_briefs)
test("RAG block contains HISTORICAL INTELLIGENCE header", "HISTORICAL INTELLIGENCE" in rag_block)
test("RAG block contains DO NOT repeat", "DO NOT repeat" in rag_block)
test("RAG block contains past query 1", "rust async" in rag_block)
test("RAG block contains past query 2", "python async" in rag_block)
test("RAG block contains angle 1", "Tokio internals" in rag_block)
test("RAG block contains title 2", "asyncio Hidden Costs" in rag_block)
test("RAG block contains differentiation instruction", "distinct from all" in rag_block)

# Estimate token cost (rough: 1 token ≈ 4 chars)
token_est = len(rag_block) / 4
test(f"RAG block token estimate reasonable ({token_est:.0f} tokens)", 50 < token_est < 300,
     f"got {token_est:.0f}")

# Test that _build_prompt accepts retrieved_briefs
prompt = _build_prompt(
    query="test query",
    signals=[{"source": "hn", "title": "Test", "score": 0.5, "url": "http://test.com"}],
    clusters=[],
    sources=[],
    revision=0,
    evaluation=None,
    retrieved_briefs=sample_briefs,
)
test("Prompt contains RAG block", "HISTORICAL INTELLIGENCE" in prompt)
test("Prompt still contains core sections", "TOP SIGNALS" in prompt and "DEEP SOURCE CONTENT" in prompt)

# Test without RAG (backward compat)
prompt_no_rag = _build_prompt(
    query="test query",
    signals=[{"source": "hn", "title": "Test", "score": 0.5, "url": "http://test.com"}],
    clusters=[], sources=[], revision=0, evaluation=None,
    retrieved_briefs=[],
)
test("No RAG → no HISTORICAL INTELLIGENCE block", "HISTORICAL INTELLIGENCE" not in prompt_no_rag)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[5/6] Pipeline Graph Structure")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from pipeline import pipeline

graph = pipeline.get_graph()
nodes = list(graph.nodes.keys())

test("Pipeline has rag_retriever node", "rag_retriever" in nodes)
test("Pipeline has all 6 agent nodes", all(
    n in nodes for n in ["trend_scout", "content_analyzer", "deep_researcher",
                          "rag_retriever", "brief_synthesizer", "strict_evaluator"]
))
test("Pipeline has increment_revision node", "increment_revision" in nodes)

# Verify edge connectivity: deep_researcher → rag_retriever → brief_synthesizer
edges = [(e.source, e.target) for e in graph.edges]
test("Edge: deep_researcher → rag_retriever", ("deep_researcher", "rag_retriever") in edges)
test("Edge: rag_retriever → brief_synthesizer", ("rag_retriever", "brief_synthesizer") in edges)
test("No direct edge: deep_researcher → brief_synthesizer",
     ("deep_researcher", "brief_synthesizer") not in edges,
     "old edge still exists!")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[6/6] Initial State Completeness")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from pipeline import run_pipeline, stream_pipeline
import inspect

# Check that run_pipeline and stream_pipeline include retrieved_briefs in initial state
run_src = inspect.getsource(run_pipeline)
stream_src = inspect.getsource(stream_pipeline)
test("run_pipeline initial state has retrieved_briefs", "retrieved_briefs" in run_src)
test("stream_pipeline initial state has retrieved_briefs", "retrieved_briefs" in stream_src)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 70)
print(f"  Results: {passed} passed, {failed} failed, {passed + failed} total")
print("=" * 70)

if failed == 0:
    print("\n  🎉 ALL TESTS PASSED — RAG integration is fully working!\n")
else:
    print(f"\n  ⚠  {failed} test(s) failed — review above.\n")
    sys.exit(1)
