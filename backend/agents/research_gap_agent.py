# Research Gap Agent: Fetches recent research papers and uses Ollama to identify
# genuine research gaps — areas that exist but are underexplored or contradicted.
# Output is a list of 5 gap topics the user can pick from, similar to Trend Agent.

import json
import random
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests
from crewai import Agent, Crew, Task
from dotenv import load_dotenv
from llm_factory import get_llm

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

OUTPUT_FILE = BASE_DIR / "output" / "research_gap_output.json"

# ── Config ────────────────────────────────────────────────────────────────────

# ArXiv categories to scan
ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "stat.ML"]
PAPERS_PER_CAT = 10

# ── Research paper fetcher ────────────────────────────────────────────────────

_HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_arxiv(category: str, broad_topic: str = "", max_results: int = PAPERS_PER_CAT) -> tuple[str, list[dict]]:
    """Fetch recent papers from one research paper category. Returns (category, papers)."""
    try:
        if broad_topic:
            # Wrap in quotes for phrase search; let urlencode handle encoding
            query = f'cat:{category} AND all:"{broad_topic}"'
        else:
            query = f"cat:{category}"
        # Random start offset — keep small so it stays within typical result counts
        start = random.randint(0, 15)
        params = {
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "start": start,
            "max_results": max_results,
        }
        url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
        resp = requests.get(url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", "", ns) or "").strip().replace("\n", " ")
            abstract = (entry.findtext("atom:summary", "", ns) or "").strip().replace("\n", " ")[:400]
            link = (entry.findtext("atom:id", "", ns) or "").strip()
            if title:
                papers.append({"title": title, "abstract": abstract, "link": link})
        print(f"  [{category}] {len(papers)} papers fetched", flush=True)
        return category, papers
    except Exception as e:
        print(f"  [{category}] Failed: {e}", flush=True)
        return category, []


# ── Gap analysis via CrewAI + Ollama ──────────────────────────────────────────


def find_gaps(papers: list[dict], broad_topic: str = "") -> list[dict]:
    # Shuffle so each run sees a different ordering / subset of papers
    shuffled = papers.copy()
    random.shuffle(shuffled)
    subset = random.sample(shuffled, min(20, len(shuffled))) if len(shuffled) > 20 else shuffled

    papers_text = "\n\n".join(f"Title: {p['title']}\nAbstract: {p['abstract']}" for p in subset)

    llm = get_llm("RESEARCH_GAP", temperature=0.9)

    analyst = Agent(
        role="AI Research Gap Analyst",
        goal="Identify genuine research gaps and novel directions from recent AI papers",
        backstory=(
            "You are a senior AI researcher who reads recent papers and spots what's missing, "
            "underexplored, or contradicted in the literature. You always respond in English."
        ),
        llm=llm,
        verbose=False,
    )

    topic_line = f"Topic to focus on: {broad_topic}\n\n" if broad_topic else ""
    seed = random.randint(1000, 9999)

    # Rotate the analytical lens each run so results are genuinely different
    _ANGLES = [
        "Focus on practical deployment and real-world scalability challenges.",
        "Focus on theoretical limitations and mathematical open problems.",
        "Focus on efficiency, speed, and resource/compute constraints.",
        "Focus on robustness, safety, alignment, and failure modes.",
        "Focus on multi-modal, cross-domain, or cross-lingual applications.",
        "Focus on data quality, dataset bias, and annotation limitations.",
        "Focus on evaluation metrics and benchmarking gaps.",
        "Focus on interpretability, explainability, and trustworthiness.",
        "Focus on low-resource, few-shot, or zero-shot scenarios.",
        "Focus on continual learning, catastrophic forgetting, and adaptation.",
    ]
    angle = random.choice(_ANGLES)

    task = Task(
        description=f"""IMPORTANT: Respond in English only. [run-id:{seed}]

{topic_line}Analytical lens for this run: {angle}

Below are recent research papers. Identify 5 genuine research gaps through the lens above — areas that are underexplored, missing, or where open questions remain unanswered.

RECENT PAPERS:
{papers_text}

For each gap produce ONE line in this exact format:
N. [Short research topic title (8-12 words)] | [One sentence explaining the specific gap]

Example:
1. Efficient fine-tuning of vision-language models on edge devices | Most VLM fine-tuning work assumes cloud-scale compute, leaving the sub-1B parameter edge deployment space unexplored.

Return exactly 5 lines. No extra text.""",
        expected_output="Exactly 5 lines in the format: N. [Title] | [Gap description]",
        agent=analyst,
    )

    crew = Crew(agents=[analyst], tasks=[task], verbose=False)
    result = str(crew.kickoff()).strip()

    gaps = []
    for line in result.splitlines():
        line = line.strip()
        match = re.match(r"^\d+[\.\)]\s*(.+)$", line)
        if not match:
            continue
        content = match.group(1).strip()
        if "|" in content:
            title, gap = content.split("|", 1)
            gaps.append({"topic": title.strip(), "gap": gap.strip()})
        elif content:
            gaps.append({"topic": content, "gap": ""})

    return gaps[:5]


# ── Main agent function ────────────────────────────────────────────────────────


def discover_research_gaps(broad_topic: str = "") -> dict:
    print("Research Gap Agent: Fetching recent research papers...", flush=True)
    if broad_topic:
        print(f'  Broad area: "{broad_topic}"', flush=True)

    all_papers: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(ARXIV_CATEGORIES)) as executor:
        futures = {executor.submit(fetch_arxiv, cat, broad_topic): cat for cat in ARXIV_CATEGORIES}
        for future in as_completed(futures):
            _, papers = future.result()
            all_papers.extend(papers)

    print(f"  {len(all_papers)} papers collected. Identifying research gaps...", flush=True)

    gaps = find_gaps(all_papers, broad_topic)

    print("\n  Research gaps found:")
    for i, g in enumerate(gaps, 1):
        print(f"    {i}. {g['topic']}")
        if g.get("gap"):
            print(f"       Gap: {g['gap']}")

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "broad_topic": broad_topic or "General AI/ML",
        "papers_scanned": len(all_papers),
        "gaps": gaps,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print(f"\nResearch Gap Agent: Done! Found {len(gaps)} gaps.")
    return output


if __name__ == "__main__":
    broad_topic = sys.argv[1] if len(sys.argv) > 1 else ""
    discover_research_gaps(broad_topic)
