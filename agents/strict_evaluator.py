# NicheSignal v5 — strict_evaluator.py — debugged & optimized 2026-04-24
"""
Evaluates briefs with 6 YouTuber-specific dimensions using Groq (llama-3.1-8b-instant).
Returns dimension_scores, weakest_dimension, critique_rationale.
Pass threshold: >= 0.72.
"""

import os
import json
from groq import Groq
from state import NicheSignalState
from event_bus import emit_event

PASS_THRESHOLD = 0.72

DIMENSIONS = {
    "producibility": 0.20,
    "search_demand_confidence": 0.20,
    "audience_fit": 0.15,
    "competitive_moat": 0.20,
    "actionability": 0.15,
    "novelty": 0.10,
}


def _groq_chat(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        api_key = os.getenv("\ufeffGROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Set it in .env.")
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return (response.choices[0].message.content or "").strip()


def _build_prompt(brief: dict, sources: list[dict]) -> str:
    source_block = ""
    if sources:
        source_block = "\n".join(
            "- [{}] {}: {}".format(
                s.get('source_name', '?'),
                s.get('url', ''),
                s.get('extracted_text', '')[:500]
            )
            for s in sources[:3]
        )
    else:
        source_block = "No source content available."

    evidence_str = json.dumps(brief.get("evidence_trail", {}))
    roadmap_str = json.dumps(brief.get("technical_roadmap", []))
    seo_str = json.dumps(brief.get("seo_keywords", []))
    risk_str = json.dumps(brief.get("risk_flags", []))

    prompt = (
        "You are a ruthless content brief evaluator for YouTube creators. Score with brutal honesty.\n\n"
        "BRIEF TO EVALUATE:\n"
        "Title: " + brief.get("suggested_title", "") + "\n"
        "Hook: " + brief.get("suggested_hook", "") + "\n"
        "Gap Summary: " + brief.get("gap_summary", "") + "\n"
        "Why Now: " + brief.get("why_now", "") + "\n"
        "Content Angle: " + brief.get("content_angle", "") + "\n"
        "Technical Roadmap: " + roadmap_str + "\n"
        "SEO Keywords: " + seo_str + "\n"
        "Risk Flags: " + risk_str + "\n"
        "Evidence Trail: " + evidence_str + "\n\n"
        "SOURCE CONTENT (evidence must be grounded in this):\n"
        + source_block + "\n\n"
        "SCORING RUBRIC — 6 YouTuber-specific dimensions (each 0.0–1.0):\n\n"
        "PRODUCIBILITY (weight 0.20): Can a solo creator execute this in under 10 hours?\n"
        "- 0.0-0.3: Requires team/budget/access most creators don't have\n"
        "- 0.7-1.0: One person with a laptop and screen recorder can ship this\n\n"
        "SEARCH_DEMAND_CONFIDENCE (weight 0.20): Is there real query volume?\n"
        "- 0.0-0.3: People talk about it but don't search for tutorials\n"
        "- 0.7-1.0: Clear search intent — people type this into YouTube/Google\n\n"
        "AUDIENCE_FIT (weight 0.15): Does this match the stated niche?\n"
        "- 0.0-0.3: Topic drifts far from the niche\n"
        "- 0.7-1.0: Dead-center in the target audience's interests\n\n"
        "COMPETITIVE_MOAT (weight 0.20): How few videos already cover this well?\n"
        "- 0.0-0.3: 10+ good videos already exist on this exact angle\n"
        "- 0.7-1.0: Virtually no one has covered this specific angle\n\n"
        "ACTIONABILITY (weight 0.15): Does the roadmap give a clear execution path?\n"
        "- 0.0-0.3: Vague steps, creator needs significant additional research\n"
        "- 0.7-1.0: Creator can open a script doc and start writing immediately\n\n"
        "NOVELTY (weight 0.10): Is the angle differentiated from existing top videos?\n"
        "- 0.0-0.3: Standard take that already exists\n"
        "- 0.7-1.0: Genuinely first-mover framing\n\n"
        "Overall = (producibility * 0.20) + (search_demand_confidence * 0.20) + "
        "(audience_fit * 0.15) + (competitive_moat * 0.20) + (actionability * 0.15) + (novelty * 0.10)\n\n"
        'Return ONLY valid JSON with these exact keys: '
        '"producibility", "search_demand_confidence", "audience_fit", "competitive_moat", '
        '"actionability", "novelty", "overall", "weakest_dimension", "critique_rationale". '
        "All score values must be floats between 0.0 and 1.0.\n\n"
        "No preamble. No markdown fences. No explanation outside the JSON."
    )
    return prompt


def strict_evaluator(state: NicheSignalState) -> dict:
    brief = state.get("brief")
    sources = state.get("full_source_content", [])
    revision = state.get("revision", 0)

    emit_event(f"[strict_evaluator] Evaluating brief (revision {revision})...")

    if not brief or not brief.get("suggested_title"):
        emit_event("[strict_evaluator] ⚠ No valid brief to evaluate")
        eval_result = {
            "passed_evaluation": False,
            "score": 0.0,
            "dimension_scores": {d: 0.0 for d in DIMENSIONS},
            "weakest_dimension": "all",
            "critique_rationale": "No valid brief was generated."
        }
        return {
            "evaluation": eval_result,
            "passed_evaluation": False,
            "log_events": ["strict_evaluator: no brief to evaluate"]
        }

    try:
        raw = _groq_chat(_build_prompt(brief, sources))
        start_idx = raw.find('{')
        end_idx = raw.rfind('}')
        if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
            raise ValueError("No JSON object found in response")

        json_str = raw[start_idx:end_idx + 1]
        data = json.loads(json_str)

        emit_event(f"[strict_evaluator] LLM returned keys: {list(data.keys())}")

        # Robust extraction: scores may be at top-level or nested
        def _find_score(key: str) -> float:
            if key in data:
                try:
                    return float(data[key])
                except (ValueError, TypeError):
                    pass
            for v in data.values():
                if isinstance(v, dict) and key in v:
                    try:
                        return float(v[key])
                    except (ValueError, TypeError):
                        pass
            return 0.0

        dimension_scores = {}
        for dim in DIMENSIONS:
            dimension_scores[dim] = max(0.0, min(1.0, _find_score(dim)))

        # Compute weighted overall
        overall = round(sum(
            dimension_scores[dim] * weight for dim, weight in DIMENSIONS.items()
        ), 3)

        # Find weakest dimension
        weakest = min(dimension_scores, key=dimension_scores.get)
        critique = str(data.get("critique_rationale", ""))
        if not critique:
            for v in data.values():
                if isinstance(v, dict) and "critique_rationale" in v:
                    critique = str(v["critique_rationale"])
                    break

        passed = overall >= PASS_THRESHOLD
        status = "PASSED ✓" if passed else "BELOW THRESHOLD ✗"

        emit_event(
            f"[strict_evaluator] Score: {overall:.2f} — {status} "
            f"(weakest: {weakest} = {dimension_scores[weakest]:.2f})"
        )

        eval_result = {
            "passed_evaluation": passed,
            "score": overall,
            "dimension_scores": dimension_scores,
            "weakest_dimension": weakest,
            "critique_rationale": critique,
        }

        return {
            "evaluation": eval_result,
            "passed_evaluation": passed,
            "log_events": [f"strict_evaluator: score={overall:.3f}, passed={passed}"]
        }

    except Exception as e:
        emit_event(f"[strict_evaluator] ⚠ Error — {e}")
        eval_result = {
            "passed_evaluation": False,
            "score": 0.0,
            "dimension_scores": {d: 0.0 for d in DIMENSIONS},
            "weakest_dimension": "error",
            "critique_rationale": f"Evaluation error: {e}"
        }
        return {
            "evaluation": eval_result,
            "passed_evaluation": False,
            "log_events": [f"strict_evaluator: error — {e}"]
        }
