# NicheSignal v5 — deep_researcher.py — debugged & optimized 2026-04-24
"""
Fetches top signal URLs concurrently, extracts main text via BeautifulSoup4.
Returns structured list[dict] with source attribution.
Truncates at sentence boundary (~800 tokens ≈ ~3200 chars).
"""

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from state import NicheSignalState
from event_bus import emit_event

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
MAX_CHARS = 3200
MAX_URLS = 3


def _truncate_at_sentence(text: str, max_chars: int) -> str:
    """Truncate text at the last sentence boundary within max_chars."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Find the last sentence-ending punctuation
    for sep in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
        last_pos = truncated.rfind(sep)
        if last_pos > max_chars // 2:
            return truncated[:last_pos + 1].strip()
    return truncated.strip()


def _source_name_from_signal(signal: dict) -> str:
    """Map signal source to a human-readable source name."""
    source = signal.get("source", "").split("/")[0]
    name_map = {
        "hackernews": "Hacker News",
        "github_trending": "GitHub Trending",
        "stackoverflow": "Stack Overflow",
        "devto": "Dev.to",
        "lobsters": "Lobsters",
        "google_trends": "Google Trends",
    }
    return name_map.get(source, source)


def _extract_page_text(url: str, timeout: int = 15) -> str:
    """Fetch URL and return cleaned main-body text."""
    response = requests.get(url, headers=_HEADERS, timeout=timeout)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "iframe", "svg"]):
        tag.decompose()

    main_content = soup.find("article") or soup.find("main") or soup.find("body") or soup
    text = main_content.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def _fetch_and_process(url: str, signal: dict) -> dict:
    raw_text = _extract_page_text(url)
    extracted = _truncate_at_sentence(raw_text, MAX_CHARS)
    source_name = _source_name_from_signal(signal)
    return {
        "url": url,
        "source_name": source_name,
        "extracted_text": extracted,
    }


def deep_researcher(state: NicheSignalState) -> dict:
    top_signals = state.get("top_signals", [])
    urls_signals = [(s.get("url", ""), s) for s in top_signals[:MAX_URLS] if s.get("url")]

    if not urls_signals:
        emit_event("[deep_researcher] ⚠ No URLs to fetch")
        return {
            "full_source_content": [],
            "log_events": ["deep_researcher: no URLs found in top_signals"]
        }

    emit_event(f"[deep_researcher] Fetching {len(urls_signals)} sources concurrently...")
    results: list[dict] = []
    log_msgs: list[str] = []

    with ThreadPoolExecutor(max_workers=MAX_URLS) as executor:
        future_to_url = {executor.submit(_fetch_and_process, url, signal): url for url, signal in urls_signals}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                res = future.result()
                results.append(res)
                token_est = len(res["extracted_text"].split())
                emit_event(f"[deep_researcher] Fetched {url[:60]}… — extracted ~{token_est} tokens")
                log_msgs.append(f"deep_researcher: fetched {url[:50]} ({token_est} tokens)")
            except Exception as e:
                emit_event(f"[deep_researcher] ⚠ Failed: {url[:50]}… — {e}")
                log_msgs.append(f"deep_researcher: failed {url[:50]} — {e}")

    emit_event(f"[deep_researcher] ✓ {len(results)}/{len(urls_signals)} sources extracted")
    log_msgs.append(f"deep_researcher: {len(results)} sources extracted")

    return {
        "full_source_content": results,
        "log_events": log_msgs
    }
