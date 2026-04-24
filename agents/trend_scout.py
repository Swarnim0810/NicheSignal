# NicheSignal v5 — trend_scout.py — debugged & optimized 2026-04-24
"""
Scrapes 6 free sources concurrently: HN, GitHub Trending, Stack Overflow, Dev.to, Lobsters, Google Trends.
Reddit is fully excluded from this project.
"""

import requests
from bs4 import BeautifulSoup
from pytrends.request import TrendReq
from datetime import datetime, timezone
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from state import NicheSignalState
from event_bus import emit_event


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scrape_hn(query: str, limit: int = 10) -> list[dict]:
    signals = []
    try:
        url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage={limit}"
        r = requests.get(url, timeout=10)
        data = r.json()
        for hit in data.get("hits", []):
            score = hit.get("points", 0) or 0
            title = hit.get("title", "")
            sig = {
                "source": "hackernews",
                "title": title,
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "score": min(score / 500, 1.0),
                "tags": ["hackernews"],
                "fetched_at": _now()
            }
            signals.append(sig)
            emit_event(f"[HN] \"{title[:60]}\" — score {sig['score']:.2f}")
    except Exception:
        emit_event("[HN] ⚠ scrape failed")
    return signals


def _scrape_github_trending(query: str) -> list[dict]:
    signals = []
    try:
        url = "https://github.com/trending"
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        repos = soup.select("article.Box-row")[:10]
        q_lower = query.lower()
        for repo in repos:
            name_el = repo.select_one("h2 a")
            desc_el = repo.select_one("p")
            stars_el = repo.select_one("span[id*='stargazers']") or repo.select_one(".d-inline-block.float-sm-right")
            if not name_el:
                continue
            name = name_el.get_text(strip=True).replace("\n", "").replace(" ", "")
            desc = desc_el.get_text(strip=True) if desc_el else ""
            if q_lower not in name.lower() and q_lower not in desc.lower():
                continue
            stars_text = stars_el.get_text(strip=True) if stars_el else "0"
            stars = int(re.sub(r"[^\d]", "", stars_text) or 0)
            title = f"{name}: {desc}"[:120]
            sig = {
                "source": "github_trending",
                "title": title,
                "url": f"https://github.com/{name}",
                "score": min(stars / 5000, 1.0),
                "tags": ["github", "trending"],
                "fetched_at": _now()
            }
            signals.append(sig)
            emit_event(f"[GitHub] \"{title[:60]}\" — score {sig['score']:.2f}")
    except Exception:
        emit_event("[GitHub] ⚠ scrape failed")
    return signals


def _scrape_stackoverflow(query: str, limit: int = 5) -> list[dict]:
    signals = []
    try:
        url = (
            f"https://api.stackexchange.com/2.3/search/advanced"
            f"?order=desc&sort=activity&q={query}&site=stackoverflow&pagesize={limit}"
        )
        r = requests.get(url, timeout=10)
        data = r.json()
        for item in data.get("items", []):
            score = item.get("score", 0)
            view_count = item.get("view_count", 0)
            title = item.get("title", "")
            sig = {
                "source": "stackoverflow",
                "title": title,
                "url": item.get("link", ""),
                "score": min((score + view_count / 1000) / 200, 1.0),
                "tags": item.get("tags", []) + ["stackoverflow"],
                "fetched_at": _now()
            }
            signals.append(sig)
            emit_event(f"[SO] \"{title[:60]}\" — score {sig['score']:.2f}")
    except Exception:
        emit_event("[SO] ⚠ scrape failed")
    return signals


def _scrape_devto(query: str, limit: int = 5) -> list[dict]:
    signals = []
    try:
        url = f"https://dev.to/api/articles?per_page={limit}&tag={query.replace(' ', '')}"
        r = requests.get(url, timeout=10)
        articles = r.json() if r.status_code == 200 else []
        for article in articles:
            reactions = article.get("positive_reactions_count", 0)
            title = article.get("title", "")
            sig = {
                "source": "devto",
                "title": title,
                "url": article.get("url", ""),
                "score": min(reactions / 500, 1.0),
                "tags": article.get("tag_list", []) + ["devto"],
                "fetched_at": _now()
            }
            signals.append(sig)
            emit_event(f"[Dev.to] \"{title[:60]}\" — score {sig['score']:.2f}")
    except Exception:
        emit_event("[Dev.to] ⚠ scrape failed")
    return signals


def _scrape_lobsters(query: str, limit: int = 5) -> list[dict]:
    signals = []
    try:
        url = "https://lobste.rs/hottest.json"
        r = requests.get(url, timeout=10)
        stories = r.json() if r.status_code == 200 else []
        q_lower = query.lower()
        count = 0
        for story in stories:
            if count >= limit:
                break
            title = story.get("title", "")
            if q_lower not in title.lower() and not any(q_lower in t for t in story.get("tags", [])):
                continue
            sig = {
                "source": "lobsters",
                "title": title,
                "url": story.get("url", ""),
                "score": min(story.get("score", 0) / 50, 1.0),
                "tags": story.get("tags", []) + ["lobsters"],
                "fetched_at": _now()
            }
            signals.append(sig)
            emit_event(f"[Lobsters] \"{title[:60]}\" — score {sig['score']:.2f}")
            count += 1
    except Exception:
        emit_event("[Lobsters] ⚠ scrape failed")
    return signals


def _scrape_google_trends(query: str) -> list[dict]:
    signals = []
    try:
        pytrends = TrendReq(hl="en-US", tz=0, timeout=(5, 15))
        pytrends.build_payload([query], timeframe="now 7-d")
        related = pytrends.related_queries()
        if query in related:
            rising = related[query].get("rising")
            if rising is not None and not rising.empty:
                for _, row in rising.head(5).iterrows():
                    title = f"Trending: {row['query']}"
                    sig = {
                        "source": "google_trends",
                        "title": title,
                        "url": f"https://trends.google.com/trends/explore?q={row['query']}",
                        "score": min(row.get("value", 0) / 5000, 1.0),
                        "tags": ["google_trends", "rising"],
                        "fetched_at": _now()
                    }
                    signals.append(sig)
                    emit_event(f"[Trends] \"{title[:60]}\" — score {sig['score']:.2f}")
    except Exception:
        emit_event("[Trends] ⚠ scrape failed")
    return signals


def trend_scout(state: NicheSignalState) -> dict:
    query = state["query"]
    emit_event(f"[trend_scout] Starting scan for: \"{query}\"")
    all_signals: list[dict] = []

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_scrape_hn, query, 10): "hn",
            executor.submit(_scrape_github_trending, query): "github",
            executor.submit(_scrape_stackoverflow, query, 5): "so",
            executor.submit(_scrape_devto, query, 5): "devto",
            executor.submit(_scrape_lobsters, query, 5): "lobsters",
            executor.submit(_scrape_google_trends, query): "trends",
        }
        for future in as_completed(futures):
            try:
                res = future.result()
                all_signals.extend(res)
            except Exception as e:
                emit_event(f"[trend_scout] ⚠ Thread error on {futures[future]}: {e}")

    emit_event(f"[trend_scout] ✓ Complete — {len(all_signals)} signals collected")

    return {
        "signals": all_signals,
        "log_events": [f"trend_scout: {len(all_signals)} signals from 6 sources"]
    }