# Agent 2: Organize raw AI news into a structured technical report
# using a local Ollama model via CrewAI.
# Section headings are derived from the content itself — not a fixed template.

import json
from datetime import datetime, timezone
from pathlib import Path

from crewai import Agent, Crew, Task
from dotenv import load_dotenv
from llm_factory import get_llm

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

INPUT_FILE = BASE_DIR / "output" / "researcher_output.json"
OUTPUT_FILE = BASE_DIR / "output" / "analyst_output.json"

# ── Config ────────────────────────────────────────────────────────────────────

TOKENS = json.loads((BASE_DIR.parent / "config" / "tokens.json").read_text())

# ── Main agent function ────────────────────────────────────────────────────────


def organize_content() -> dict:
    print("Agent 2: Organizing content into a structured report...")

    raw_data = json.loads(INPUT_FILE.read_text())
    articles = raw_data["articles"]

    articles_text = "\n\n---\n\n".join(
        f"Title: {a['title']}\nContent: {a.get('full_content') or a['snippet']}\nLink: {a['link']}" for a in articles
    )

    llm = get_llm("ANALYST")

    topic = raw_data.get("topic", "Latest AI updates")

    analyst = Agent(
        role="Senior AI Research Analyst",
        goal="Produce a comprehensive, insightful technical report from AI news articles using headings that best fit the content",
        backstory=(
            "You are a senior AI researcher with deep expertise in machine learning, "
            "LLMs, and AI systems. You write clear, insightful technical reports in English only. "
            "You never use a fixed template — you read the content first, then decide what sections "
            "will best capture the story the articles are telling."
        ),
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""IMPORTANT: Respond in English only. Do not use any other language.

Topic: {topic}

Read the following AI news articles carefully, then write a comprehensive technical report about them.

ARTICLES:
{articles_text}

Instructions:
- Decide 6 to 9 section headings yourself based on what themes, patterns, and stories actually emerge from these articles.
- Do NOT use a fixed or pre-defined set of headings like "Introduction / Advantages / Disadvantages".
- Headings should be specific and descriptive — they should reflect the actual content, not generic categories.
  Good examples: "The Shift Toward Smaller, Efficient Models", "Why Context Windows Now Matter More Than Parameters",
  "How Three Labs Are Racing Toward the Same Goal", "The Open-Source vs. Closed-Source Tension".
  Bad examples: "Introduction", "Advantages", "Conclusion".
- Each section should be substantive: 3-6 bullet points or 2-4 sentences of real analysis, not just restatements.
- Reference specific models, companies, researchers, or numbers from the articles where relevant.
- Use markdown formatting with `##` for section headings.
- End with one short section that names the most important unanswered question raised by these articles.""",
        expected_output="A markdown-formatted technical report with 6-9 content-driven section headings derived from the articles.",
        agent=analyst,
    )

    crew = Crew(agents=[analyst], tasks=[task], verbose=False)
    result = crew.kickoff()
    report = str(result)

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "topic": topic,
        "source_articles": len(articles),
        "report": report,
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print("Agent 2: Done! Report generated with content-driven sections.")
    return output


if __name__ == "__main__":
    organize_content()
