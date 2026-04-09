# Agent 1: Fetch the latest AI news using Google News RSS (parallel), then use
# a local Ollama model (via CrewAI) to organize results into structured JSON.
# Searches active sources in parallel batches of 3. If a batch yields too few
# articles, randomly picks 3 more from inactive sources and retries.

import json
import os
import random
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests
from crewai import Agent, Crew, LLM, Task
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

OUTPUT_FILE = BASE_DIR / "output" / "researcher_output.json"

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

CONFIG_DIR = BASE_DIR.parent / "config"

SOURCES = json.loads((CONFIG_DIR / "sources.json").read_text())
TOKENS  = json.loads((CONFIG_DIR / "tokens.json").read_text())

# All sources as a label → object lookup (active and inactive)
ALL_SOURCES_BY_LABEL = {
    s["label"]: {"query": s["query"], "label": s["label"], "category": cat}
    for cat, items in SOURCES.items()
    for s in items
}

ACTIVE_SOURCES = [
    ALL_SOURCES_BY_LABEL[s["label"]]
    for cat, items in SOURCES.items()
    for s in items
    if s.get("enabled", True)
]

# Minimum articles per batch before triggering fallback
MIN_ARTICLES_PER_BATCH = 3

TREND_OUTPUT = BASE_DIR / "output" / "trend_output.json"

def get_trend_sources() -> tuple[list[dict], list[dict]]:
    """
    Return (primary, fallback) source lists.
    If trend_output.json exists, primary = sources the trend agent used.
    Otherwise, primary = active sources from sources.json.
    Fallback = everything not in primary.
    """
    if TREND_OUTPUT.exists():
        try:
            trend = json.loads(TREND_OUTPUT.read_text())
            scanned_labels = trend.get("sources_scanned", [])
            if scanned_labels:
                primary  = [ALL_SOURCES_BY_LABEL[l] for l in scanned_labels if l in ALL_SOURCES_BY_LABEL]
                used     = set(scanned_labels)
                fallback = [s for s in ALL_SOURCES_BY_LABEL.values() if s["label"] not in used]
                print(f"  Using trend agent sources: {', '.join(scanned_labels)}")
                return primary, fallback
        except Exception as e:
            print(f"  Could not read trend_output.json ({e}), using active sources.")
    return ACTIVE_SOURCES, [
        s for s in ALL_SOURCES_BY_LABEL.values()
        if s["label"] not in {a["label"] for a in ACTIVE_SOURCES}
    ]

# ── Google News RSS helper ────────────────────────────────────────────────────

_GNEWS_RSS = "https://news.google.com/rss/search"
_HEADERS   = {"User-Agent": "Mozilla/5.0"}

def gnews_search(source: dict, topic: str = "", max_results: int = 5) -> tuple[dict, list[dict]]:
    """Fetch articles for one source. Returns (source, articles) for use in futures."""
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
            desc = ET.fromstring(f"<d>{desc}</d>").text if desc.startswith("<") else desc
            articles.append({
                "title":    item.findtext("title", ""),
                "snippet":  desc or "",
                "link":     item.findtext("link", ""),
                "source":   source["label"],
                "category": source["category"],
                "date":     item.findtext("pubDate", ""),
            })
        return source, articles
    except Exception as e:
        print(f"  [ERROR]     {source['label']}: {e}")
        return source, []

# ── Parallel batch search ─────────────────────────────────────────────────────

def search_batch_parallel(sources: list[dict], topic: str = "", max_results: int = 5) -> list[dict]:
    """Search a list of sources in parallel, logging each start and completion."""
    all_articles = []
    print(f"  Launching {len(sources)} parallel searches...", flush=True)

    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        futures = {}
        for source in sources:
            print(f"  [SEARCHING] {source['label']}...", flush=True)
            futures[executor.submit(gnews_search, source, topic, max_results)] = source["label"]

        for future in as_completed(futures):
            source, articles = future.result()
            count = len(articles)
            print(f"  [DONE]      {source['label']} — {count} article{'s' if count != 1 else ''} found", flush=True)
            all_articles.extend(articles)

    return all_articles

# ── Main agent function ────────────────────────────────────────────────────────

def fetch_latest_ai_concepts(topic: str = "") -> dict:
    primary_sources, fallback_sources = get_trend_sources()

    print(f"Agent 1: Starting research across {len(primary_sources)} primary sources", flush=True)
    if topic:
        print(f"  Topic: \"{topic}\"", flush=True)

    remaining_fallbacks = fallback_sources.copy()
    random.shuffle(remaining_fallbacks)

    raw_articles  = []
    sources_used  = []
    batch_num     = 0

    # Split primary sources into batches of 3 and search each batch
    active_batches = [primary_sources[i:i+3] for i in range(0, len(primary_sources), 3)]

    for batch in active_batches:
        batch_num += 1
        batch_names = [s["label"] for s in batch]
        print(f"\n  Batch {batch_num} (primary): {', '.join(batch_names)}", flush=True)

        batch_articles = search_batch_parallel(batch, topic)
        raw_articles.extend(batch_articles)
        sources_used.extend(batch_names)
        print(f"  Batch {batch_num} total: {len(batch_articles)} articles | Running total: {len(raw_articles)}", flush=True)

        # If this batch was too thin, queue a fallback batch immediately after
        if len(batch_articles) < MIN_ARTICLES_PER_BATCH and remaining_fallbacks:
            fallback_batch = remaining_fallbacks[:3]
            remaining_fallbacks = remaining_fallbacks[3:]
            fb_names = [s["label"] for s in fallback_batch]
            print(f"\n  Batch {batch_num} returned only {len(batch_articles)} articles — "
                  f"trying fallback: {', '.join(fb_names)}")
            batch_num += 1
            fb_articles = search_batch_parallel(fallback_batch, topic)
            raw_articles.extend(fb_articles)
            sources_used.extend(fb_names)
            print(f"  Fallback batch total: {len(fb_articles)} articles | Running total: {len(raw_articles)}")

    # If still very few results, drain remaining fallbacks in batches of 3
    while len(raw_articles) < MIN_ARTICLES_PER_BATCH and remaining_fallbacks:
        fallback_batch = remaining_fallbacks[:3]
        remaining_fallbacks = remaining_fallbacks[3:]
        fb_names = [s["label"] for s in fallback_batch]
        batch_num += 1
        print(f"\n  Still only {len(raw_articles)} articles total — "
              f"trying next fallback batch: {', '.join(fb_names)}")
        fb_articles = search_batch_parallel(fallback_batch, topic)
        raw_articles.extend(fb_articles)
        sources_used.extend(fb_names)
        print(f"  Batch total: {len(fb_articles)} articles | Running total: {len(raw_articles)}")

    print(f"\n  Raw results: {len(raw_articles)} articles collected across {len(sources_used)} sources.")
    print("  Organizing with Ollama...")

    # Step 2: Use CrewAI + Ollama to filter and structure results
    llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)

    raw_text = "\n\n".join(
        f"[{a['source']} | {a['category']}]\nTitle: {a['title']}\nSnippet: {a['snippet']}\nURL: {a['link']}"
        for a in raw_articles
    )

    topic_line = f'Focus specifically on: "{topic}"\n\n' if topic else ""

    analyst = Agent(
        role="AI News Curator",
        goal="Select and organize the most relevant AI news articles into structured JSON",
        backstory="You are a senior AI research curator who selects the most informative and unique articles. You ALWAYS respond in English only.",
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""IMPORTANT: Respond in English only. Do not use any other language.

{topic_line}From the raw search results below, select the best 20-25 unique and informative articles.
Remove duplicates and low-quality results.

RAW RESULTS:
{raw_text}

Return ONLY a raw JSON array — no explanation, no markdown fences:
[
  {{
    "title": "article title",
    "snippet": "2-3 sentence summary",
    "link": "full URL",
    "source": "source name",
    "category": "research | lab_blogs | newsletters | news | community",
    "date": null
  }}
]""",
        expected_output="A raw JSON array of article objects with no markdown or extra text.",
        agent=analyst,
    )

    crew        = Crew(agents=[analyst], tasks=[task], verbose=False)
    result      = crew.kickoff()
    output_text = str(result)

    # Parse JSON from agent output
    articles = []
    try:
        json_match = re.search(r"\[[\s\S]*\]", output_text)
        if json_match:
            articles = json.loads(json_match.group())
        else:
            raise ValueError("No JSON array found in agent output")
    except Exception as err:
        print(f"  Could not parse agent JSON ({err}), using raw results.")
        articles = raw_articles

    output = {
        "timestamp":        datetime.utcnow().isoformat(),
        "topic":            topic or "Latest AI updates",
        "total":            len(articles),
        "sources_searched": sources_used,
        "articles":         articles,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print(f"Agent 1: Done! Found {len(articles)} articles across {len(sources_used)} sources.")
    return output


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else ""
    fetch_latest_ai_concepts(topic)
