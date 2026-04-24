# NicheSignal v5 — app.py — UI redesign 2026-04-24
"""
Streamlit UI with sidebar history, live feed, structured card layout,
plotly evaluation scorecard, and export functionality. Redesigned with a dark editorial magazine aesthetic.
"""

import streamlit as st
import sys
import os
import time
import json
import threading
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"), override=True)

HISTORY_FILE = os.path.join(BASE_DIR, "query_history.json")

st.set_page_config(page_title="NicheSignal", page_icon="📡", layout="wide", initial_sidebar_state="expanded")

# ── THEME TRACKING ───────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

def toggle_theme():
    if st.session_state["theme"] == "dark":
        st.session_state["theme"] = "light"
    else:
        st.session_state["theme"] = "dark"

# ── CSS (Dark Editorial Magazine) ────────────────────────────────────────────
dark_css_vars = """
    --bg: #0D0A08;
    --surface: #161009;
    --surface-hover: #1F1710;
    --border: #2A1F15;
    --border-subtle: #3A2E25;
    --text: #F0E6D3;
    --text-muted: #8A7A6A;
    --accent: #E8824A;
    --accent-dark: #B85F2D;
    --pass: #5DBD7A;
    --fail: #D9534F;
    --pill-bg: #2A1F15;
"""

light_css_vars = """
    --bg: #F5EFE6;
    --surface: #FFFFFF;
    --surface-hover: #F9F6F0;
    --border: #E0D5C1;
    --border-subtle: #D0C5B1;
    --text: #1A1A1A;
    --text-muted: #6B6154;
    --accent: #E8824A;
    --accent-dark: #C66A38;
    --pass: #3A9D57;
    --fail: #C9332F;
    --pill-bg: #EAE2D3;
"""

current_vars = light_css_vars if st.session_state["theme"] == "light" else dark_css_vars

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=Inter:wght@400;500;600&display=swap');

:root {{
    {current_vars}
}}

html, body, .stApp, [class*="css"] {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
}}

h1, h2, h3, .hero-title {{
    font-family: 'Playfair Display', serif !important;
    color: var(--text) !important;
}}

/* Hero Section */
.hero-wrapper {{
    text-align: center;
    padding: 3rem 1rem 2rem 1rem;
    position: relative;
}}
.hero-wrapper::before {{
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 60%;
    height: 60%;
    background: radial-gradient(circle, rgba(232,130,74,0.05) 0%, rgba(13,10,8,0) 70%);
    z-index: 0;
    pointer-events: none;
}}
.hero-content {{ position: relative; z-index: 1; }}
.hero-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    color: var(--text-muted);
    text-transform: uppercase;
    margin-bottom: 1rem;
}}
.hero-title {{
    font-size: 3.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    line-height: 1.1;
}}
.hero-title span {{
    font-style: italic;
    color: var(--accent);
}}
.hero-subtitle {{
    font-size: 1rem;
    color: var(--text-muted);
    max-width: 600px;
    margin: 0 auto 2rem auto;
    line-height: 1.6;
}}
.hero-divider {{
    color: var(--text-muted);
    letter-spacing: 0.5em;
    font-size: 0.8rem;
    margin-bottom: 2rem;
}}

/* Search Bar */
.search-container {{
    max-width: 600px;
    margin: 0 auto 2rem auto;
}}
.stTextInput > div > div > input {{
    border-radius: 50px !important;
    background: var(--surface) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text) !important;
    padding: 16px 24px !important;
    font-size: 16px !important;
    font-family: 'Inter', sans-serif !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: var(--bg) !important;
    border-right: 1px solid var(--border) !important;
}}
.sidebar-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    color: var(--text-muted);
    text-transform: uppercase;
    margin-bottom: 0.25rem;
}}
.sidebar-title {{
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 1rem;
}}
.sidebar-divider {{
    height: 1px;
    background: var(--border);
    margin-bottom: 1rem;
}}
.sidebar-pill {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.sidebar-pill:hover {{
    border-color: var(--accent);
    background: var(--surface-hover);
}}
.sidebar-pill-text {{
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: 0.05em;
    text-transform: uppercase;
}}
.badge-pass {{
    color: var(--pass);
    font-weight: 600;
    font-size: 0.7rem;
}}
.badge-fail {{
    color: var(--fail);
    font-weight: 600;
    font-size: 0.7rem;
}}

/* Cards & Brief Content */
.editorial-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
}}
.card-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 12px;
}}
.gap-summary {{
    font-size: 1.25rem;
    line-height: 1.6;
    color: var(--text);
    font-weight: 500;
}}
.why-now-box {{
    border-left: 3px solid var(--accent);
    padding-left: 1rem;
    margin-top: 1rem;
    color: var(--text-muted);
    font-size: 0.95rem;
    line-height: 1.6;
}}
.evidence-pill {{
    display: inline-block;
    background: var(--pill-bg);
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    color: var(--text);
    margin: 0 6px 6px 0;
}}
.evidence-pill.hn {{ color: #E8824A; border-color: rgba(232,130,74,0.3); }}
.evidence-pill.so {{ color: #5B9BD5; border-color: rgba(91,155,213,0.3); }}
.evidence-pill.devto {{ color: #A45EE5; border-color: rgba(164,94,229,0.3); }}
.evidence-pill.lobsters {{ color: #5DBD7A; border-color: rgba(93,189,122,0.3); }}
.evidence-stats {{
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-top: 12px;
    line-height: 1.5;
}}
.evidence-stats strong {{ color: var(--text); }}

.brief-header-title {{
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 1rem;
    line-height: 1.2;
}}
.brief-metadata-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    font-size: 0.8rem;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: 0.75rem 0;
    margin-bottom: 1.5rem;
}}
.meta-item {{ display: flex; flex-direction: column; }}
.meta-label {{ color: var(--text-muted); letter-spacing: 0.1em; font-size: 0.65rem; text-transform: uppercase; margin-bottom: 2px; }}
.meta-value {{ color: var(--text); font-weight: 500; }}
.meta-value.accent {{ color: var(--accent); }}

.theme-pill {{
    display: inline-block;
    background: var(--pill-bg);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    color: var(--accent);
    margin: 0 6px 6px 0;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}}

.hook-text {{ font-style: italic; color: var(--text-muted); margin-bottom: 1rem; font-size: 1.05rem; }}
.angle-box {{ background: rgba(232,130,74,0.05); border: 1px solid rgba(232,130,74,0.2); border-radius: 8px; padding: 16px; font-size: 0.95rem; line-height: 1.6; }}

.roadmap-step {{
    display: flex;
    margin-bottom: 1rem;
    align-items: flex-start;
}}
.step-number {{
    color: var(--accent);
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    font-weight: 700;
    margin-right: 12px;
    min-width: 24px;
}}
.step-text {{ font-size: 0.95rem; line-height: 1.5; color: var(--text); padding-top: 2px; }}

/* Live Feed */
.log-feed {{
    background: #0A0705;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    color: #8A7A6A;
    max-height: 300px;
    overflow-y: auto;
    line-height: 1.5;
}}
.log-hn {{ color: #E8824A; }}
.log-so {{ color: #5B9BD5; }}
.log-synth {{ color: #D4A843; }}
.log-eval {{ color: #5DBD7A; }}

/* Buttons */
.stButton > button {{
    border-radius: 50px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}}
.stButton > button:hover {{
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}}

/* Theme Toggle */
.theme-toggle-btn {{
    position: absolute;
    top: 1rem;
    left: 1rem;
    z-index: 100;
}}
</style>
""", unsafe_allow_html=True)


# ── History helpers ──────────────────────────────────────────────────────────
def _load_history() -> list[dict]:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_history(history: list[dict]):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def _append_history(query: str, score: float, passed: bool, brief: dict, evaluation: dict):
    history = _load_history()
    history.insert(0, {
        "query": query,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "score": score,
        "passed": passed,
        "brief": brief,
        "evaluation": evaluation
    })
    _save_history(history[:50])


# ── Brief to Markdown (for export) ───────────────────────────────────────────
def _brief_to_markdown(brief: dict, evaluation: dict | None) -> str:
    lines = [f"# NicheSignal Brief: {brief.get('suggested_title', 'Untitled')}", ""]
    lines.append(f"## Gap Summary\n{brief.get('gap_summary', '')}\n")
    lines.append(f"## Why Now\n{brief.get('why_now', '')}\n")
    lines.append(f"## Content Angle\n{brief.get('content_angle', '')}\n")
    lines.append(f"## Suggested Title\n**{brief.get('suggested_title', '')}**\n")
    lines.append(f"## Suggested Hook\n*{brief.get('suggested_hook', '')}*\n")
    trail = brief.get("evidence_trail", {})
    if trail:
        lines.append(f"## Evidence Trail")
        lines.append(f"- Sources: {', '.join(trail.get('sources_list', []))}")
        lines.append(f"- Signal count: {trail.get('signal_count', 0)}")
        lines.append(f"- Common pattern: {trail.get('common_complaint_pattern', '')}\n")
    roadmap = brief.get("technical_roadmap", [])
    if roadmap:
        lines.append("## Technical Roadmap")
        for i, step in enumerate(roadmap, 1):
            lines.append(f"{i}. {step}")
        lines.append("")
    kws = brief.get("seo_keywords", [])
    if kws:
        lines.append(f"## SEO Keywords\n{', '.join(kws)}\n")
    risks = brief.get("risk_flags", [])
    if risks:
        lines.append("## Risk Flags")
        for r in risks:
            lines.append(f"⚠️ {r}")
        lines.append("")
    if evaluation:
        lines.append(f"## Evaluation Score: {evaluation.get('score', 0):.0%}")
        for dim, val in evaluation.get("dimension_scores", {}).items():
            lines.append(f"- {dim}: {val:.2f}")
    return "\n".join(lines)


# ── Theme Toggle Button ──────────────────────────────────────────────────────
col_t1, col_t2 = st.columns([1, 10])
with col_t1:
    btn_label = "☀ LIGHT" if st.session_state["theme"] == "dark" else "🌙 DARK"
    if st.button(btn_label, key="theme_toggle"):
        toggle_theme()
        st.rerun()


# ── Hero Section ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrapper">
    <div class="hero-content">
        <div class="hero-label">POWERED BY AI · MULTI-SOURCE · ONE BRIEF</div>
        <div class="hero-title">NicheSignal <span>Intelligence</span></div>
        <div class="hero-subtitle">Enter a niche keyword — six sources get scraped, signals get clustered, and a content brief gets built for your next video.</div>
        <div class="hero-divider">— ✦ —</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Search Bar ───────────────────────────────────────────────────────────────
query = ""
col_search_empty, col_search_main, col_search_empty2 = st.columns([1, 6, 1])
with col_search_main:
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    query = st.text_input("query", placeholder="Search a niche keyword...", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
col_btn_empty, col_btn_main, col_btn_empty2 = st.columns([3, 2, 3])
with col_btn_main:
    run = st.button("Run Pipeline ▶", use_container_width=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div class='sidebar-label'>COLLECTION</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>Query History</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    history = _load_history()
    if not history:
        st.caption("No queries yet.")

    for i, entry in enumerate(history[:15]):
        badge_class = "badge-pass" if entry.get("passed") else "badge-fail"
        badge_text = "PASS" if entry.get("passed") else "FAIL"
        
        html = f"""
        <div class='sidebar-pill'>
            <div class='sidebar-pill-text'>🔖 {entry['query'][:25]}</div>
            <div class='{badge_class}'>{badge_text}</div>
        </div>
        """
        # We use a button overlay to make it clickable
        if st.button(f"Load: {entry['query'][:20]}...", key=f"hist_{i}", use_container_width=True):
            st.session_state["loaded_brief"] = entry.get("brief", {})
            st.session_state["loaded_eval"] = entry.get("evaluation", {})
            st.session_state["loaded_query"] = entry.get("query", "")


# ── Render brief cards ───────────────────────────────────────────────────────
def render_brief(brief: dict, evaluation: dict | None, display_query: str):
    if not brief or not brief.get("suggested_title"):
        st.markdown("<div class='editorial-card'>No valid brief to display.</div>", unsafe_allow_html=True)
        return

    st.markdown("---")
    
    # Topic Header Block
    title = brief.get("suggested_title", "Untitled")
    trail = brief.get("evidence_trail", {})
    sources = trail.get("sources_list", [])
    src_count = trail.get("sources_count", 0)
    sig_count = trail.get("signal_count", 0)
    
    st.markdown(f"<div class='brief-header-title'>\"{title}\"</div>", unsafe_allow_html=True)
    
    meta_html = f"""
    <div class='brief-metadata-row'>
        <div class='meta-item'>
            <div class='meta-label'>NICHE</div>
            <div class='meta-value accent'>{display_query.upper()}</div>
        </div>
        <div class='meta-item'>
            <div class='meta-label'>SOURCES</div>
            <div class='meta-value'>{src_count}</div>
        </div>
        <div class='meta-item'>
            <div class='meta-label'>SIGNALS</div>
            <div class='meta-value'>{sig_count}</div>
        </div>
        <div class='meta-item'>
            <div class='meta-label'>TOP SOURCES</div>
            <div class='meta-value'>{', '.join(sources[:3])}</div>
        </div>
    </div>
    """
    st.markdown(meta_html, unsafe_allow_html=True)
    
    # Themes / Keywords
    kws = brief.get("seo_keywords", [])
    if kws:
        kws_html = "".join(f"<span class='theme-pill'>#{k.replace(' ', '-')}</span>" for k in kws)
        st.markdown(f"<div style='margin-bottom:2rem'>{kws_html}</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.5, 1])

    with col1:
        # Card 1: Gap Summary & Why Now
        st.markdown(f"""
        <div class='editorial-card'>
            <div class='card-label'>GAP SUMMARY</div>
            <div class='gap-summary'>{brief.get('gap_summary', '')}</div>
            <div class='why-now-box'><strong>Why Now:</strong> {brief.get('why_now', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Card 2: Content Strategy
        st.markdown(f"""
        <div class='editorial-card'>
            <div class='card-label'>CONTENT STRATEGY</div>
            <div class='hook-text'>"{brief.get('suggested_hook', '')}"</div>
            <div class='angle-box'>{brief.get('content_angle', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Card 3: Technical Roadmap
        roadmap = brief.get("technical_roadmap", [])
        if roadmap:
            roadmap_html = "<div class='editorial-card'><div class='card-label'>TECHNICAL ROADMAP</div>"
            for i, step in enumerate(roadmap, 1):
                clean_step = step.split(":", 1)[1].strip() if ":" in step and step.startswith("Step") else step
                roadmap_html += f"<div class='roadmap-step'><div class='step-number'>{i}</div><div class='step-text'>{clean_step}</div></div>"
            roadmap_html += "</div>"
            st.markdown(roadmap_html, unsafe_allow_html=True)

    with col2:
        # Card 4: Evidence Trail
        def _get_pill_class(src: str):
            src_lower = src.lower()
            if "hacker" in src_lower or "hn" in src_lower: return "hn"
            if "stack" in src_lower: return "so"
            if "dev.to" in src_lower: return "devto"
            if "lobster" in src_lower: return "lobsters"
            return ""

        src_pills = "".join(f"<span class='evidence-pill {_get_pill_class(s)}'>{s}</span>" for s in sources)
        
        st.markdown(f"""
        <div class='editorial-card'>
            <div class='card-label'>EVIDENCE TRAIL</div>
            <div style='margin-bottom:12px'>{src_pills}</div>
            <div class='evidence-stats'>
                <strong>Signals analyzed:</strong> {sig_count}<br><br>
                <strong>Common pattern:</strong><br>{trail.get('common_complaint_pattern', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Card 5: Risks
        risks = brief.get("risk_flags", [])
        if risks:
            st.warning("**RISK FLAGS**\n\n" + "\n".join(f"- {r}" for r in risks))

        # Card 6: Evaluation Scorecard
        st.markdown("<div class='editorial-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-label'>EVALUATION SCORECARD</div>", unsafe_allow_html=True)
        if evaluation:
            score = evaluation.get("score", 0)
            passed = evaluation.get("passed_evaluation", False)
            pct = int(score * 100)
            
            if passed:
                st.success(f"**PASS — {pct}%**")
            else:
                st.error(f"**FAIL — {pct}%**")
            
            dim_scores = evaluation.get("dimension_scores", {})
            if dim_scores:
                import plotly.graph_objects as go
                dims = list(dim_scores.keys())
                vals = [dim_scores[d] for d in dims]
                
                # Dark editorial chart colors
                fig = go.Figure(go.Bar(
                    x=vals, y=[d.replace("_", " ").title() for d in dims],
                    orientation='h', marker_color="#E8824A",
                    text=[f"{v:.2f}" for v in vals], textposition='outside',
                    textfont=dict(family="Inter", size=11, color="#F0E6D3"),
                ))
                fig.add_vline(x=0.72, line_dash="dash", line_color="#8A7A6A")
                bg_color = "rgba(0,0,0,0)"
                font_color = "#F0E6D3" if st.session_state["theme"] == "dark" else "#1A1A1A"
                grid_color = "#2A1F15" if st.session_state["theme"] == "dark" else "#E0D5C1"
                
                fig.update_layout(
                    plot_bgcolor=bg_color, paper_bgcolor=bg_color,
                    font=dict(family="Inter", color=font_color, size=10),
                    xaxis=dict(range=[0, 1.05], gridcolor=grid_color, showgrid=True),
                    yaxis=dict(gridcolor=grid_color), height=250, margin=dict(l=10, r=30, t=10, b=10),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

            weakest = evaluation.get("weakest_dimension", "")
            critique = evaluation.get("critique_rationale", "")
            if weakest:
                st.markdown(f"**Weakest:** {weakest.replace('_',' ').title()}<br><span style='font-size:0.85rem;color:var(--text-muted)'>{critique}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Export
    st.markdown("---")
    btn_cols = st.columns(4)
    with btn_cols[0]:
        md = _brief_to_markdown(brief, evaluation)
        st.download_button("↓ Export as Markdown", md, file_name="nichesignal_brief.md", mime="text/markdown", use_container_width=True)


# ── Show loaded history brief ────────────────────────────────────────────────
if "loaded_brief" in st.session_state and not run:
    brief = st.session_state.pop("loaded_brief", {})
    evaluation = st.session_state.pop("loaded_eval", {})
    query_text = st.session_state.pop("loaded_query", "Unknown Query")
    render_brief(brief, evaluation, query_text)
    st.stop()


# ── Pipeline execution ───────────────────────────────────────────────────────
groq_key = os.getenv("GROQ_API_KEY", "").strip() or os.getenv("\ufeffGROQ_API_KEY", "").strip()

if run and not groq_key:
    st.error("Cannot run: GROQ_API_KEY is not set.")
elif run and query.strip():
    from pipeline import run_pipeline
    from event_bus import get_events, clear_events

    clear_events()

    st.markdown("### Live Intelligence Feed")
    log_placeholder = st.empty()
    status_placeholder = st.empty()

    result_container = {}
    error_container = {}

    def _run():
        try:
            result_container["result"] = run_pipeline(query.strip())
        except Exception as e:
            error_container["error"] = str(e)

    thread = threading.Thread(target=_run)
    thread.start()

    all_logs: list[str] = []
    start_time = time.time()

    def _colorize_log(line: str) -> str:
        if "[HN]" in line: return f"<span class='log-hn'>{line}</span>"
        if "[SO]" in line: return f"<span class='log-so'>{line}</span>"
        if "synthesizer" in line.lower(): return f"<span class='log-synth'>{line}</span>"
        if "evaluator" in line.lower(): return f"<span class='log-eval'>{line}</span>"
        return line

    while thread.is_alive():
        new_events = get_events()
        all_logs.extend(new_events)
        elapsed = int(time.time() - start_time)

        visible = all_logs[-30:]
        log_html = "<div class='log-feed'>"
        for line in visible:
            log_html += _colorize_log(line) + "<br>"
        log_html += "<span style='animation: blink 1s step-end infinite'>_</span></div>"
        
        log_placeholder.markdown(log_html, unsafe_allow_html=True)
        status_placeholder.markdown(f"<div style='color:var(--text-muted);font-size:0.8rem;text-align:center;margin-top:10px;'>Running… {elapsed}s elapsed</div>", unsafe_allow_html=True)
        time.sleep(0.5)

    thread.join()

    all_logs.extend(get_events())
    status_placeholder.empty()

    visible = all_logs[-30:]
    log_html = "<div class='log-feed'>"
    for line in visible:
        log_html += _colorize_log(line) + "<br>"
    log_html += "</div>"
    log_placeholder.markdown(log_html, unsafe_allow_html=True)

    if "error" in error_container:
        st.error(f"Pipeline error: {error_container['error']}")
        st.stop()

    state = result_container.get("result", {})
    brief = state.get("brief", {})
    evaluation = state.get("evaluation", {})

    if brief and brief.get("suggested_title"):
        score = evaluation.get("score", 0) if evaluation else 0
        passed = evaluation.get("passed_evaluation", False) if evaluation else False
        _append_history(query.strip(), score, passed, brief, evaluation)

    render_brief(brief, evaluation, query.strip())
elif run and not query.strip():
    st.warning("Please enter a keyword to search.")