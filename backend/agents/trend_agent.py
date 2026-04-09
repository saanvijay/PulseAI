# Trend Agent: Search active sources for the most trending AI topic right now.
# Uses Google News RSS and a local Ollama model (via CrewAI) to identify
# the single most trending topic phrase (3-6 words).

import json
import os
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
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

SOURCES = json.loads((CONFIG_DIR / "sources.json").read_text())

ALL_SEARCHES = [
    {"query": s["query"], "label": s["label"], "category": cat}
    for cat, items in SOURCES.items()
    for s in items
    if s.get("enabled", True)
]

# ── Google News RSS helper ────────────────────────────────────────────────────

_GNEWS_RSS = "https://news.google.com/rss/search"
_HEADERS   = {"User-Agent": "Mozilla/5.0"}

def gnews_search(query: str, max_results: int = 5) -> list[dict]:
    try:
        url  = f"{_GNEWS_RSS}?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        root  = ET.fromstring(resp.content)
        items = root.findall(".//item")[:max_results]
        return [{"title": item.findtext("title", ""), "source": item.findtext("source", "")} for item in items]
    except Exception as e:
        print(f"  Google News search failed for '{query}': {e}")
        return []

# ── Main agent function ────────────────────────────────────────────────────────

def get_trending_topic() -> dict:
    source_names = ", ".join(s["label"] for s in ALL_SEARCHES)
    print(f"Trend Agent: Scanning {len(ALL_SEARCHES)} active sources for trending topics...")

    # Step 1: Search each source with Google News RSS
    snippets = []
    for source in ALL_SEARCHES:
        print(f"  Searching: \"{source['label']}\"")
        results = gnews_search(source["query"], max_results=3)
        for r in results:
            snippets.append(f"- {r.get('title', '')} ({source['label']})")

    headlines_text = "\n".join(snippets) if snippets else "No results found."

    print("  Identifying trending topic with Ollama...")

    # Step 2: Use CrewAI + Ollama to identify the single most trending topic
    llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)

    analyst = Agent(
        role="AI Trend Analyst",
        goal="Identify the single most trending AI topic from recent headlines",
        backstory="You track the AI industry daily and have a sharp eye for spotting emerging trends. You ALWAYS respond in English only.",
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""IMPORTANT: Respond in English only. Do not use any other language.

Below are the latest AI headlines from sources: {source_names}.

HEADLINES:
{headlines_text}

Based on these headlines, what is the single most trending AI topic right now?

Respond with ONLY a short topic phrase (3-6 words).
No explanation, no bullet points, no punctuation at the end. Just the phrase.

Good examples:
- LLM reasoning and planning
- Multimodal foundation models
- AI agents and autonomy
- Retrieval-augmented generation""",
        expected_output="A short 3-6 word phrase describing the most trending AI topic.",
        agent=analyst,
    )

    crew   = Crew(agents=[analyst], tasks=[task], verbose=False)
    result = crew.kickoff()
    topic  = str(result).strip().strip('"').strip("'")

    output = {
        "timestamp":       datetime.utcnow().isoformat(),
        "topic":           topic,
        "sources_scanned": [s["label"] for s in ALL_SEARCHES],
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print(f'Trend Agent: Trending topic → "{topic}"')
    return output


if __name__ == "__main__":
    get_trending_topic()
