# NicheSignal v5 — brief_synthesizer.py — debugged & optimized 2026-04-24
"""
Generates a structured 9-field content intelligence brief using Groq (llama3-70b-8192).
Injects structured source content as labeled passages. Caps tokens to avoid over-prompting.
On retries, feeds back weakest_dimension and critique_rationale.
"""

import os
import json
from groq import Groq
from state import NicheSignalState
from event_bus import emit_event


def _groq_chat(prompt: str) -> str:
    """Call Groq API with llama3-70b-8192 at temperature=0.3."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        api_key = os.getenv("\ufeffGROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Set it in .env.")
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return (response.choices[0].message.content or "").strip()


def _format_source_passages(sources: list[dict], max_total_chars: int = 8000) -> str:
    """Format full_source_content as labeled passages for the prompt.
    Caps total characters at max_total_chars (~2000 tokens) to save context.
    Truncates the longest sources first to preserve source diversity.
    """
    if not sources:
        return "No deep source content available."
        
    texts = [src.get("extracted_text", "") for src in sources]
    
    while sum(len(t) for t in texts) > max_total_chars:
        longest_idx = max(range(len(texts)), key=lambda i: len(texts[i]))
        current_len = len(texts[longest_idx])
        if current_len <= 500:
            break
        new_len = current_len - 500
        truncated = texts[longest_idx][:new_len]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        texts[longest_idx] = truncated + "..."

    blocks = []
    for i, src in enumerate(sources):
        label = src.get("source_name", f"Source {i+1}")
        url = src.get("url", "")
        text = texts[i]
        blocks.append(f"[{label}] ({url})\n{text}")
    return "\n\n---\n\n".join(blocks)


def _build_prompt(query: str, signals: list[dict], clusters: list[dict],
                  sources: list[dict], revision: int, evaluation: dict | None) -> str:
    signal_lines = "\n".join(
        f"- [{s['source']}] {s['title']} (score: {s['score']:.2f}) — {s.get('url', '')}"
        for s in signals[:8]
    )
    cluster_summary = ""
    for i, c in enumerate(clusters[:3], 1):
        cluster_summary += (
            f"\nCluster {i}: {c['representative']['title'][:80]} "
            f"| momentum: {c['momentum_score']:.2f} | {c.get('sources_found_in', '')} "
            f"| signals: {c.get('signal_count', 0)}"
        )

    source_block = _format_source_passages(sources)

    retry_block = ""
    if revision > 0 and evaluation:
        weakest = evaluation.get("weakest_dimension", "unknown")
        critique = evaluation.get("critique_rationale", "No critique provided")
        retry_block = f"""

CRITICAL RETRY CONTEXT (attempt #{revision + 1}):
Your previous attempt scored low on: **{weakest}**
The critique was: "{critique}"
You MUST specifically fix {weakest} in this version. Do not repeat the same weaknesses.
"""

    return f"""You are a senior content strategist generating intelligence briefs for mid-size YouTubers (50K–500K subs) in tech/AI/dev niches.

Query: "{query}"

TOP SIGNALS:
{signal_lines}

SIGNAL CLUSTERS:
{cluster_summary}

DEEP SOURCE CONTENT:
{source_block}
{retry_block}
Generate a structured intelligence brief as valid JSON with EXACTLY these 9 fields:
{{
  "gap_summary": "One sentence: what the audience wants that no existing content provides",
  "evidence_trail": {{
    "sources_count": 0,
    "sources_list": ["list", "of", "source", "names"],
    "common_complaint_pattern": "The recurring frustration or unanswered question across sources",
    "signal_count": 0
  }},
  "why_now": "What recent event, release, or shift is making this topic hot right now",
  "content_angle": "The specific framing that no existing video takes — must be differentiated",
  "technical_roadmap": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ...",
    "Step 4: ...",
    "Step 5: ..."
  ],
  "seo_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "risk_flags": ["Any oversaturation concerns or dominant existing videos to be aware of"],
  "suggested_title": "The YouTube title — specific, clickable, curiosity-driven",
  "suggested_hook": "Opening 2 sentences the creator should say on camera"
}}

Requirements:
- Be extremely specific. No generic advice. Reference actual signal data.
- gap_summary must identify something MISSING from existing content.
- evidence_trail must cite real sources from the signals above.
- technical_roadmap must give 5 concrete, implementation-ready steps.
- suggested_title must create a curiosity gap with a named tool/technique.
- seo_keywords must be realistic search terms people actually type.

Respond with ONLY the JSON object. No preamble, no markdown fences, no explanation."""


BRIEF_FIELDS = [
    "gap_summary", "evidence_trail", "why_now", "content_angle",
    "technical_roadmap", "seo_keywords", "risk_flags",
    "suggested_title", "suggested_hook"
]


def brief_synthesizer(state: NicheSignalState) -> dict:
    top_signals = state.get("top_signals", [])
    clusters = state.get("clusters", [])
    query = state["query"]
    revision = state.get("revision", 0)
    sources = state.get("full_source_content", [])
    evaluation = state.get("evaluation")

    attempt = revision + 1
    emit_event(f"[brief_synthesizer] Generating brief... (attempt {attempt}/3)")

    if not top_signals:
        emit_event("[brief_synthesizer] ⚠ No top signals available")
        return {
            "brief": {},
            "log_events": ["brief_synthesizer: no top signals"]
        }

    try:
        prompt = _build_prompt(query, top_signals, clusters, sources, revision, evaluation)
        raw = _groq_chat(prompt)
        start_idx = raw.find('{')
        end_idx = raw.rfind('}')
        if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
            raise ValueError("No JSON object found in response")
        
        json_str = raw[start_idx:end_idx + 1]
        brief = json.loads(json_str)

        # Validate all 9 fields are present
        missing = [f for f in BRIEF_FIELDS if f not in brief]
        if missing:
            emit_event(f"[brief_synthesizer] ⚠ Missing fields: {missing} — retrying parse")
            return {
                "brief": brief,
                "log_events": [f"brief_synthesizer: partial brief, missing {missing}"]
            }

        emit_event(f"[brief_synthesizer] ✓ Brief generated: \"{brief.get('suggested_title', '')[:60]}\"")
        return {
            "brief": brief,
            "log_events": [f"brief_synthesizer: brief generated (attempt {attempt})"]
        }

    except json.JSONDecodeError as e:
        emit_event(f"[brief_synthesizer] ⚠ JSON parse error — {e}")
        return {
            "brief": {},
            "log_events": [f"brief_synthesizer: JSON parse error — {e}"]
        }
    except Exception as e:
        emit_event(f"[brief_synthesizer] ⚠ Error — {e}")
        return {
            "brief": {},
            "log_events": [f"brief_synthesizer: {e}"]
        }