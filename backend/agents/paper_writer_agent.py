# Paper Writer Agent: Takes the synthesizer summary and the selected research gap,
# and writes a full ArXiv-format research paper using CrewAI + Ollama.

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from crewai import Agent, Crew, LLM, Task
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

SYNTH_FILE  = BASE_DIR / "output" / "synthesizer_output.json"
GAP_FILE    = BASE_DIR / "output" / "research_gap_output.json"
ANALYST_FILE= BASE_DIR / "output" / "analyst_output.json"
OUTPUT_FILE = BASE_DIR / "output" / "publisher_output.json"

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

# ── Paper writer via CrewAI + Ollama ──────────────────────────────────────────

def write_arxiv_paper(topic: str, gap: str, related_work_summary: str) -> str:
    llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)

    writer = Agent(
        role="AI Research Paper Author",
        goal="Write a rigorous, well-structured ArXiv-format research paper that addresses an identified research gap",
        backstory=(
            "You are an expert AI researcher with a strong publication record at top venues "
            "(NeurIPS, ICML, ACL, ICCV). You write clearly, precisely, and with academic rigour. "
            "You always write in English."
        ),
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""IMPORTANT: Respond in English only. Write a complete ArXiv-format research paper.

Research Topic: {topic}
Research Gap to Address: {gap}

RELATED WORK SUMMARY (synthesized from recent literature — use for Related Work section):
{related_work_summary}

Write the full paper with ALL sections below. Use exactly these headings:

**Title:** [Specific, descriptive paper title]

**Abstract**
(150-250 words) Motivate the problem, state the gap, sketch the proposed approach, and summarise expected contributions.

**1. Introduction**
- Background and motivation
- The specific research gap this paper addresses
- Why existing work falls short
- Our contributions (numbered list)

**2. Related Work**
- Summarise the existing literature from the summary above
- Group by theme or approach
- Clearly state what each line of work leaves open

**3. Problem Statement**
- Formal definition of the problem
- Assumptions and scope
- Why current solutions are insufficient

**4. Proposed Methodology**
- Proposed approach, architecture, or framework to address the gap
- Key design decisions and rationale
- Algorithm or process description (use pseudocode or step-by-step if helpful)

**5. Discussion**
- Expected results and how they would validate the approach
- Potential limitations and mitigations
- Broader impact on the research community

**6. Conclusion**
- Summary of contributions
- Future work directions

**References**
List 6-10 plausible references in this format:
[1] Author, A. et al. (Year). "Paper Title." Venue.

Write in formal academic English. Be specific and technical. Do not add any meta-commentary outside the paper.""",
        expected_output="A complete ArXiv-format research paper with Title, Abstract, and 6 numbered sections.",
        agent=writer,
    )

    crew   = Crew(agents=[writer], tasks=[task], verbose=False)
    result = crew.kickoff()
    return str(result)

# ── Resolve gap description for the current topic ─────────────────────────────

def _resolve_gap(topic: str) -> str:
    """Find the gap description for the selected topic from research_gap_output.json."""
    if not GAP_FILE.exists():
        return ""
    try:
        data = json.loads(GAP_FILE.read_text())
        for g in data.get("gaps", []):
            g_topic = g.get("topic", "").lower()
            if g_topic and (g_topic in topic.lower() or topic.lower() in g_topic):
                return g.get("gap", "")
        # fallback: return first gap description
        gaps = data.get("gaps", [])
        return gaps[0].get("gap", "") if gaps else ""
    except Exception:
        return ""

# ── Main agent function ────────────────────────────────────────────────────────

def write_research_paper() -> dict:
    print("Agent 4 (Research Mode): Writing ArXiv-format paper...", flush=True)

    synth_data    = json.loads(SYNTH_FILE.read_text())
    final_summary = synth_data.get("final_summary", "")
    topic         = synth_data.get("topic", "")

    # Fall back to analyst output for topic if synthesizer didn't save it
    if not topic and ANALYST_FILE.exists():
        analyst_data = json.loads(ANALYST_FILE.read_text())
        topic = analyst_data.get("topic", "")

    gap = _resolve_gap(topic)

    print(f"  Topic : {topic}", flush=True)
    print(f"  Gap   : {gap}", flush=True)
    print("  Generating paper with Ollama...", flush=True)

    paper = write_arxiv_paper(topic, gap, final_summary)

    print("\n" + "=" * 60)
    print("ARXIV RESEARCH PAPER")
    print("=" * 60)
    print(paper)
    print("=" * 60 + "\n")

    results = {
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "mode":          "research",
        "topic":         topic,
        "gap":           gap,
        "final_article": paper,
        "status":        "displayed",
    }

    OUTPUT_FILE.write_text(json.dumps(results, indent=2))
    print("Agent 4: Done! ArXiv paper written.", flush=True)
    return results


if __name__ == "__main__":
    write_research_paper()
