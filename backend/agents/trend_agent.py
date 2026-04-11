# Trend Agent: Search active sources for the most trending AI topics right now.
# Uses Google News RSS (parallel fetches) and a local Ollama model (via CrewAI)
# to identify the top 5 trending topic phrases for the user to choose from.
# If the primary sources return too few results, 3 fallback sources are tried.

import json
import os
import random
import re
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests
from crewai import Agent, Crew, LLM, Task
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

OUTPUT_FILE = BASE_DIR / "output" / "trend_output.json"

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

CONFIG_DIR = BASE_DIR.parent / "config"
SOURCES    = json.loads((CONFIG_DIR / "sources.json").read_text())

ACTIVE_SOURCES = [
    {"query": s["query"], "label": s["label"], "category": cat}
    for cat, items in SOURCES.items()
    for s in items
    if s.get("enabled", True)
]

FALLBACK_SOURCES = [
    {"query": s["query"], "label": s["label"], "category": cat}
    for cat, items in SOURCES.items()
    for s in items
    if not s.get("enabled", True)
]

# Minimum number of headlines before trying fallback sources
MIN_HEADLINES = 5

# ── Google News RSS helper ────────────────────────────────────────────────────

_GNEWS_RSS = "https://news.google.com/rss/search"
_HEADERS   = {"User-Agent": "Mozilla/5.0"}

def gnews_search(source: dict, max_results: int = 5) -> tuple[dict, list[dict]]:
    """Fetch headlines for one source. Returns (source, results) for use in futures."""
    try:
        url  = f"{_GNEWS_RSS}?q={urllib.parse.quote(source['query'])}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        root  = ET.fromstring(resp.content)
        items = root.findall(".//item")[:max_results]
        results = [{"title": item.findtext("title", ""), "source": item.findtext("source", "")} for item in items]
        return source, results
    except Exception as e:
        print(f"  [ERROR] {source['label']}: {e}")
        return source, []

# ── Parallel search ───────────────────────────────────────────────────────────

def search_sources_parallel(sources: list[dict], max_results: int = 5) -> list[str]:
    """Search all sources in parallel, log each as it starts and completes."""
    snippets = []
    print(f"  Launching {len(sources)} parallel searches...", flush=True)

    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        futures = {}
        for source in sources:
            print(f"  [SEARCHING] {source['label']}...", flush=True)
            futures[executor.submit(gnews_search, source, max_results)] = source["label"]

        for future in as_completed(futures):
            source, results = future.result()
            count = len(results)
            print(f"  [DONE]      {source['label']} — {count} headline{'s' if count != 1 else ''} found", flush=True)
            for r in results:
                snippets.append(f"- {r.get('title', '')} ({source['label']})")

    return snippets

# ── Main agent function ────────────────────────────────────────────────────────

def get_trending_topic() -> dict:
    print(f"Trend Agent: Scanning {len(ACTIVE_SOURCES)} active sources in parallel...", flush=True)

    # Step 1: Search active sources in parallel
    snippets = search_sources_parallel(ACTIVE_SOURCES, max_results=5)

    # Step 2: Fallback — if too few results, try 3 random inactive sources
    sources_used = [s["label"] for s in ACTIVE_SOURCES]
    if len(snippets) < MIN_HEADLINES and FALLBACK_SOURCES:
        fallback = random.sample(FALLBACK_SOURCES, min(3, len(FALLBACK_SOURCES)))
        fallback_names = [s["label"] for s in fallback]
        print(f"\n  Not enough results ({len(snippets)} headlines). "
              f"Trying fallback sources: {', '.join(fallback_names)}")
        fallback_snippets = search_sources_parallel(fallback, max_results=5)
        snippets.extend(fallback_snippets)
        sources_used.extend(fallback_names)

    print(f"\n  Total headlines collected: {len(snippets)}")

    headlines_text = "\n".join(snippets) if snippets else "No results found."

    print("  Identifying top 5 trending topics with Ollama...")

    # Step 3: Use CrewAI + Ollama to identify the top 5 trending topics
    llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)

    analyst = Agent(
        role="AI Trend Analyst",
        goal="Identify the top 5 trending AI topics from recent headlines",
        backstory="You track the AI industry daily and have a sharp eye for spotting emerging trends. You ALWAYS respond in English only.",
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""IMPORTANT: Respond in English only. Do not use any other language.

Below are the latest AI headlines from: {', '.join(sources_used)}.

HEADLINES:
{headlines_text}

Based on these headlines, identify the TOP 5 most trending AI topics right now.

Respond with EXACTLY 5 lines, one topic per line, numbered 1 to 5.
Each topic must be a short phrase (3-6 words).
No explanation, no extra text — just the 5 numbered topics.

Example format:
1. LLM reasoning and planning
2. Multimodal foundation models
3. AI agents and autonomy
4. Retrieval-augmented generation
5. Open-source model releases""",
        expected_output="Exactly 5 numbered lines, each a 3-6 word trending AI topic phrase.",
        agent=analyst,
    )

    crew        = Crew(agents=[analyst], tasks=[task], verbose=False)
    result      = crew.kickoff()
    output_text = str(result).strip()

    # Parse the numbered list into a Python list
    topics = []
    for line in output_text.splitlines():
        line  = line.strip()
        match = re.match(r"^\d+[\.\)]\s*(.+)$", line)
        if match:
            topics.append(match.group(1).strip().strip('"').strip("'"))

    # Fallback: split by newline if regex found nothing
    if not topics:
        topics = [l.strip() for l in output_text.splitlines() if l.strip()]

    topics = topics[:5]

    print("\n  Top trending topics:")
    for i, t in enumerate(topics, 1):
        print(f"    {i}. {t}")

    output = {
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "topics":          topics,
        "topic":           topics[0] if topics else "",  # backwards compatibility
        "sources_scanned": sources_used,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print(f"\nTrend Agent: Done! Found {len(topics)} trending topics.")
    return output


if __name__ == "__main__":
    get_trending_topic()
