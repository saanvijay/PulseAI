# Agent 1: Fetch detailed AI news about the selected topic using Google News RSS.
# Searches the same sources the Trend Agent used, in parallel batches of 3.
# No LLM involved — raw articles are collected directly and saved as-is.

import json
import os
import random
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

OUTPUT_FILE  = BASE_DIR / "output" / "researcher_output.json"
TREND_OUTPUT = BASE_DIR / "output" / "trend_output.json"

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG_DIR = BASE_DIR.parent / "config"

SOURCES = json.loads((CONFIG_DIR / "sources.json").read_text())
TOKENS  = json.loads((CONFIG_DIR / "tokens.json").read_text())

# All sources as a label → object lookup
ALL_SOURCES_BY_LABEL = {
    s["label"]: {"query": s["query"], "label": s["label"], "category": cat}
    for cat, items in SOURCES.items()
    for s in items
}

# Researcher uses ALL sources from these categories regardless of "enabled" flag
# (enabled flag is only used by the Trend Agent)
RESEARCHER_CATEGORIES   = {"lab_blogs", "newsletters", "news", "community"}
RESEARCHER_FALLBACK_CAT = {"research"}

RESEARCHER_PRIMARY_SOURCES = [
    {"query": s["query"], "label": s["label"], "category": cat}
    for cat, items in SOURCES.items()
    for s in items
    if cat in RESEARCHER_CATEGORIES
]

RESEARCHER_FALLBACK_SOURCES = [
    {"query": s["query"], "label": s["label"], "category": cat}
    for cat, items in SOURCES.items()
    for s in items
    if cat in RESEARCHER_FALLBACK_CAT
]

# Articles fetched per source
ARTICLES_PER_SOURCE = 3

# Minimum articles per batch before triggering a fallback batch
MIN_ARTICLES_PER_BATCH = 3

# ── Source selection ──────────────────────────────────────────────────────────

def get_primary_and_fallback() -> tuple[list[dict], list[dict]]:
    """
    Primary = trend agent's sources first (so the topic-relevant sources lead),
              followed by all other researcher-category sources not already in that set.
    Fallback = research category (arxiv etc.) — only used if primary yields nothing.
    If no trend output exists, primary = all researcher-category sources.
    """
    trend_labels = []
    if TREND_OUTPUT.exists():
        try:
            trend = json.loads(TREND_OUTPUT.read_text())
            trend_labels = trend.get("sources_scanned", [])
            if trend_labels:
                print(f"  Trend agent used: {', '.join(trend_labels)}", flush=True)
        except Exception as e:
            print(f"  Could not read trend_output.json ({e}).", flush=True)

    # Build primary: trend sources first, then all remaining researcher sources
    trend_set = set(trend_labels)
    trend_sources  = [ALL_SOURCES_BY_LABEL[l] for l in trend_labels if l in ALL_SOURCES_BY_LABEL]
    other_sources  = [s for s in RESEARCHER_PRIMARY_SOURCES if s["label"] not in trend_set]
    primary        = trend_sources + other_sources

    print(f"  Primary sources ({len(primary)}): {', '.join(s['label'] for s in primary)}", flush=True)
    return primary, RESEARCHER_FALLBACK_SOURCES

# ── Google News RSS ───────────────────────────────────────────────────────────

_GNEWS_RSS = "https://news.google.com/rss/search"
_HEADERS   = {"User-Agent": "Mozilla/5.0"}

def gnews_search(source: dict, topic: str, max_results: int = ARTICLES_PER_SOURCE) -> tuple[dict, list[dict]]:
    """Fetch articles for one source. Returns (source, articles)."""
    query = f"{topic} {source['query']}" if topic else source["query"]
    try:
        url  = f"{_GNEWS_RSS}?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        root  = ET.fromstring(resp.content)
        items = root.findall(".//item")[:max_results]
        articles = []
        for item in items:
            desc = item.findtext("description", "")
            if desc.startswith("<"):
                try:
                    desc = ET.fromstring(f"<d>{desc}</d>").text or ""
                except Exception:
                    desc = ""
            articles.append({
                "title":    item.findtext("title", ""),
                "snippet":  desc.strip(),
                "link":     item.findtext("link", ""),
                "source":   source["label"],
                "category": source["category"],
                "date":     item.findtext("pubDate", ""),
            })
        return source, articles
    except Exception as e:
        print(f"  [ERROR]     {source['label']}: {e}", flush=True)
        return source, []

# ── Parallel batch search ─────────────────────────────────────────────────────

def search_batch_parallel(sources: list[dict], topic: str, max_results: int = ARTICLES_PER_SOURCE) -> list[dict]:
    """Search a batch of sources in parallel, logging each start and completion."""
    all_articles = []
    print(f"  Launching {len(sources)} parallel searches...", flush=True)

    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        futures = {
            executor.submit(gnews_search, source, topic, max_results): source
            for source in sources
        }
        for source in sources:
            print(f"  [SEARCHING] {source['label']}...", flush=True)

        for future in as_completed(futures):
            source, articles = future.result()
            count = len(articles)
            print(f"  [DONE]      {source['label']} [{source['category']}] — {count} article{'s' if count != 1 else ''} found", flush=True)
            all_articles.extend(articles)

    return all_articles

# ── Main agent function ────────────────────────────────────────────────────────

def fetch_latest_ai_concepts(topic: str = "") -> dict:
    primary_sources, fallback_sources = get_primary_and_fallback()

    print(f"Agent 1: Fetching articles from {len(primary_sources)} primary sources", flush=True)
    if topic:
        print(f"  Topic: \"{topic}\"", flush=True)

    remaining_fallbacks = fallback_sources.copy()
    random.shuffle(remaining_fallbacks)

    raw_articles = []
    sources_used = []
    batch_num    = 0

    # Search primary sources in batches of 3
    primary_batches = [primary_sources[i:i+3] for i in range(0, len(primary_sources), 3)]

    for batch in primary_batches:
        batch_num  += 1
        batch_names = [s["label"] for s in batch]
        print(f"\n  Batch {batch_num} (primary): {', '.join(batch_names)}", flush=True)

        batch_articles = search_batch_parallel(batch, topic)
        raw_articles.extend(batch_articles)
        sources_used.extend(batch_names)
        print(f"  Batch {batch_num}: {len(batch_articles)} articles | Total so far: {len(raw_articles)}", flush=True)

        # Too thin — pull a fallback batch immediately
        if len(batch_articles) < MIN_ARTICLES_PER_BATCH and remaining_fallbacks:
            fallback_batch  = remaining_fallbacks[:3]
            remaining_fallbacks = remaining_fallbacks[3:]
            fb_names        = [s["label"] for s in fallback_batch]
            batch_num      += 1
            print(f"\n  Only {len(batch_articles)} articles — fallback batch {batch_num}: {', '.join(fb_names)}", flush=True)
            fb_articles = search_batch_parallel(fallback_batch, topic)
            raw_articles.extend(fb_articles)
            sources_used.extend(fb_names)
            print(f"  Fallback batch {batch_num}: {len(fb_articles)} articles | Total so far: {len(raw_articles)}", flush=True)

    # Still too few — drain remaining fallbacks
    while len(raw_articles) < MIN_ARTICLES_PER_BATCH and remaining_fallbacks:
        fallback_batch      = remaining_fallbacks[:3]
        remaining_fallbacks = remaining_fallbacks[3:]
        fb_names            = [s["label"] for s in fallback_batch]
        batch_num          += 1
        print(f"\n  Still only {len(raw_articles)} articles — trying: {', '.join(fb_names)}", flush=True)
        fb_articles = search_batch_parallel(fallback_batch, topic)
        raw_articles.extend(fb_articles)
        sources_used.extend(fb_names)
        print(f"  Batch {batch_num}: {len(fb_articles)} articles | Total so far: {len(raw_articles)}", flush=True)

    # Deduplicate by link
    seen  = set()
    unique_articles = []
    for a in raw_articles:
        if a["link"] not in seen:
            seen.add(a["link"])
            unique_articles.append(a)

    print(f"\n  {len(unique_articles)} unique articles collected from {len(sources_used)} sources.", flush=True)

    output = {
        "timestamp":        datetime.utcnow().isoformat(),
        "topic":            topic or "Latest AI updates",
        "total":            len(unique_articles),
        "sources_searched": sources_used,
        "articles":         unique_articles,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print(f"Agent 1: Done! {len(unique_articles)} articles saved.", flush=True)
    return output


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else ""
    fetch_latest_ai_concepts(topic)
