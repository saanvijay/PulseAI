# Agent 2: Organize raw AI news into a structured 8-section technical report
# using a local Ollama model via CrewAI.

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from crewai import Agent, Crew, LLM, Task
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

INPUT_FILE  = BASE_DIR / "output" / "researcher_output.json"
OUTPUT_FILE = BASE_DIR / "output" / "analyst_output.json"

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

sys.path.insert(0, str(BASE_DIR))
from config.tokens import TOKENS

# ── Main agent function ────────────────────────────────────────────────────────

def organize_content() -> dict:
    print("Agent 2: Organizing content into a structured report...")

    raw_data = json.loads(INPUT_FILE.read_text())
    articles = raw_data["articles"]

    articles_text = "\n\n---\n\n".join(
        f"Title: {a['title']}\nSnippet: {a['snippet']}\nLink: {a['link']}"
        for a in articles
    )

    llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)

    analyst = Agent(
        role="Senior AI Research Analyst",
        goal="Produce a comprehensive, structured technical report from AI news articles",
        backstory=(
            "You are a senior AI researcher with deep expertise in machine learning, "
            "LLMs, and AI systems. You write clear, insightful technical reports."
        ),
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""Based on the following AI news articles, create a comprehensive structured technical report.

ARTICLES:
{articles_text}

Create a detailed report with EXACTLY these 8 sections:

1. **Introduction**
   - Overview of the latest trends found in the articles
   - Why this matters to the AI community

2. **Existing Problems**
   - Key challenges and limitations currently faced in AI
   - Problems that motivated these new developments

3. **Proposed Solutions**
   - New approaches, methods, or models introduced
   - How they address the existing problems

4. **Architecture Overview**
   - A simple ASCII diagram showing how the new AI systems work
   - Key components and their relationships

5. **Advantages**
   - Benefits of the new developments
   - What improvements they bring

6. **Disadvantages**
   - Limitations, risks, or concerns
   - What still needs to be solved

7. **Applied AI Use Cases**
   - Real-world applications of these developments
   - Industries that will benefit

8. **Future Implementation**
   - What to expect next in AI
   - Predictions and upcoming milestones

Keep each section concise but informative. Use bullet points where appropriate.""",
        expected_output="A markdown-formatted 8-section technical report covering the AI news.",
        agent=analyst,
    )

    crew   = Crew(agents=[analyst], tasks=[task], verbose=False)
    result = crew.kickoff()
    report = str(result)

    output = {
        "timestamp":       datetime.utcnow().isoformat(),
        "source_articles": len(articles),
        "report":          report,
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print("Agent 2: Done! Report organized with 8 sections.")
    return output


if __name__ == "__main__":
    organize_content()
