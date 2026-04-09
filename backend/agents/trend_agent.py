# Trend Agent: Search active sources for the most trending AI topic right now.
# Uses DuckDuckGo for search and a local Ollama model (via CrewAI) to identify
# the single most trending topic phrase (3-6 words).

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

OUTPUT_FILE = BASE_DIR / "output" / "trend_output.json"

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

sys.path.insert(0, str(BASE_DIR))
from config.sources import SOURCES

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

def get_trending_topic() -> dict:
    source_names = ", ".join(s["label"] for s in ALL_SEARCHES)
    print(f"Trend Agent: Scanning {len(ALL_SEARCHES)} active sources for trending topics...")

    # Step 1: Search each source with DuckDuckGo
    snippets = []
    for source in ALL_SEARCHES:
        print(f"  Searching: \"{source['label']}\"")
        results = ddg_search(source["query"], max_results=3)
        for r in results:
            snippets.append(f"- {r.get('title', '')} ({source['label']})")

    headlines_text = "\n".join(snippets) if snippets else "No results found."

    print("  Identifying trending topic with Ollama...")

    # Step 2: Use CrewAI + Ollama to identify the single most trending topic
    llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)

    analyst = Agent(
        role="AI Trend Analyst",
        goal="Identify the single most trending AI topic from recent headlines",
        backstory="You track the AI industry daily and have a sharp eye for spotting emerging trends.",
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""Below are the latest AI headlines from sources: {source_names}.

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
