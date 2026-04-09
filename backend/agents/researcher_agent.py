# Agent 1: Fetch the latest AI news using DuckDuckGo search, then use
# a local Ollama model (via CrewAI) to organize results into structured JSON.

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from crewai import Agent, Crew, LLM, Task
from duckduckgo_search import DDGS
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

OUTPUT_FILE = BASE_DIR / "output" / "researcher_output.json"

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

# Add parent to path so config imports work when run directly
sys.path.insert(0, str(BASE_DIR))
from config.sources import SOURCES
from config.tokens import TOKENS

ALL_SEARCHES = [
    {"query": s["query"], "label": s["label"], "category": cat}
    for cat, items in SOURCES.items()
    for s in items
]

# ── DuckDuckGo helper ─────────────────────────────────────────────────────────

def ddg_search(query: str, max_results: int = 5) -> list[dict]:
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        print(f"  DDG search failed for '{query}': {e}")
        return []

# ── Main agent function ────────────────────────────────────────────────────────

def fetch_latest_ai_concepts(topic: str = "") -> dict:
    source_names = ", ".join(s["label"] for s in ALL_SEARCHES)
    print(f"Agent 1: Searching {len(ALL_SEARCHES)} sources — {source_names}")
    if topic:
        print(f"  Topic: \"{topic}\"")

    # Step 1: Search all sources with DuckDuckGo
    raw_articles = []
    for source in ALL_SEARCHES:
        query = f"{topic} {source['query']}" if topic else source["query"]
        print(f"  Searching: \"{source['label']}\"")
        results = ddg_search(query, max_results=5)
        for r in results:
            raw_articles.append({
                "title":    r.get("title", ""),
                "snippet":  r.get("body", ""),
                "link":     r.get("href", ""),
                "source":   source["label"],
                "category": source["category"],
                "date":     None,
            })

    print(f"  Raw results: {len(raw_articles)} articles collected. Organizing with Ollama...")

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
        backstory="You are a senior AI research curator who selects the most informative and unique articles.",
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""{topic_line}From the raw search results below, select the best 20-25 unique and informative articles.
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

    crew   = Crew(agents=[analyst], tasks=[task], verbose=False)
    result = crew.kickoff()
    output_text = str(result)

    # Parse JSON from agent output
    articles = []
    try:
        json_match = __import__("re").search(r"\[[\s\S]*\]", output_text)
        if json_match:
            articles = json.loads(json_match.group())
        else:
            raise ValueError("No JSON array found in agent output")
    except Exception as err:
        print(f"  Could not parse agent JSON ({err}), using raw DDG results.")
        articles = raw_articles

    output = {
        "timestamp":        datetime.utcnow().isoformat(),
        "topic":            topic or "Latest AI updates",
        "total":            len(articles),
        "sources_searched": [s["label"] for s in ALL_SEARCHES],
        "articles":         articles,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print(f"Agent 1: Done! Found {len(articles)} results across {len(ALL_SEARCHES)} sources.")
    return output


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else ""
    fetch_latest_ai_concepts(topic)
