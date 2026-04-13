# Paper Writer Agent: Takes the synthesizer summary and the selected research gap,
# and writes a research paper using CrewAI + Ollama or a cloud model.
#
# Output length:
#   Local model  → compact draft (~2-3 pages, 6 sections)
#   Cloud model  → full academic paper (~12-15 pages, 9 sections + references)

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from crewai import Agent, Crew, Task
from dotenv import load_dotenv
from llm_factory import get_llm, is_cloud_provider

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

SYNTH_FILE   = BASE_DIR / "output" / "synthesizer_output.json"
GAP_FILE     = BASE_DIR / "output" / "research_gap_output.json"
ANALYST_FILE = BASE_DIR / "output" / "analyst_output.json"
OUTPUT_FILE  = BASE_DIR / "output" / "publisher_output.json"

# ── Prompts ───────────────────────────────────────────────────────────────────

def _local_prompt(topic: str, gap: str, related_work: str) -> str:
    """Compact prompt for local models — realistic for 7B parameter models."""
    return f"""IMPORTANT: Respond in English only. Write a concise research paper draft.

Research Topic: {topic}
Research Gap: {gap}

RELATED WORK SUMMARY:
{related_work}

Write a draft with these sections:

**Title:** [Specific, descriptive title]

**Abstract**
150-250 words. Motivate the problem, state the gap, sketch the approach, summarise contributions.

**1. Introduction**
Background, motivation, the specific gap, why existing work falls short, contributions (numbered list).

**2. Related Work**
Summarise existing literature from the summary above. Group by theme. State what each leaves open.

**3. Problem Statement**
Formal problem definition, assumptions, scope, why current solutions are insufficient.

**4. Proposed Methodology**
Proposed approach or framework. Key design decisions. Algorithm or step-by-step if helpful.

**5. Discussion**
Expected results, potential limitations, broader impact.

**6. Conclusion**
Summary of contributions and future work directions.

**References**
6-10 entries: [N] Author et al. (Year). "Title." Venue.

Write in formal academic English. Be specific and technical."""


def _cloud_prompt(topic: str, gap: str, related_work: str) -> str:
    """Full academic paper prompt for cloud models — targets 12-15 pages (~6000-8000 words)."""
    return f"""IMPORTANT: Respond in English only.

You are a senior AI researcher writing a full-length academic paper for submission to a top venue (NeurIPS, ICML, ACL, ICCV). Write every section in depth — this paper should be 12 to 15 pages long (approximately 6000 to 8000 words total). Do not truncate any section. Every section must be substantive.

Research Topic: {topic}
Research Gap Being Addressed: {gap}

RELATED WORK SUMMARY (synthesized from recent literature — use as the foundation for Section 3):
{related_work}

---

Write the complete paper using EXACTLY these sections and headings. Each section length target is given — hit it.

**Title**
A specific, descriptive, publication-quality paper title.

**Authors**
PulseAI Research Pipeline (AI-Assisted Draft)

**Abstract** (250–300 words)
- What problem is being solved and why it matters
- The specific research gap this paper addresses
- The proposed approach at a high level
- Key expected contributions and their significance
- One sentence on evaluation approach

**Keywords**
5–8 relevant technical keywords separated by commas.

**1. Introduction** (700–900 words)
1.1 Background and Context
  - Situate the problem in the broader AI/ML landscape
  - Why this area has received attention recently
1.2 Motivation
  - Concrete real-world scenarios where the gap causes problems
  - Why solving this matters now
1.3 The Research Gap
  - Precisely what is missing in the literature
  - Why existing approaches fail to address it
1.4 Our Approach
  - High-level description of the proposed solution
  - Key intuition behind the approach
1.5 Contributions
  Numbered list of 4–6 specific, concrete contributions
1.6 Paper Organisation
  One sentence per section describing what each covers.

**2. Background & Preliminaries** (400–600 words)
- Define all key concepts, terminology, and notation used throughout the paper
- Provide mathematical definitions where appropriate
- Briefly explain foundational methods the proposed approach builds on
- Keep accessible to a reader familiar with ML but not the specific sub-field

**3. Related Work** (900–1100 words)
Organise into 4–6 thematic subsections, each covering a distinct line of related work.
For each subsection:
  - Describe what the existing work does and its strengths
  - Cite representative approaches from the related work summary provided
  - Clearly identify the specific limitation or gap each line of work leaves open
End with a paragraph explicitly contrasting all related work with the proposed approach.

**4. Problem Formulation** (500–700 words)
- Formal mathematical definition of the problem
- Input space, output space, and objective function
- Explicit assumptions and their justifications
- Scope and out-of-scope scenarios
- Evaluation criteria: what "solving" the problem means quantitatively

**5. Proposed Methodology** (1200–1600 words)
5.1 Overview
  - Architectural or algorithmic overview (describe a figure if one would normally appear here)
5.2 Core Components
  - Detailed description of each component of the proposed system
  - Design decisions and the rationale for each
5.3 Algorithm
  - Step-by-step algorithm description or pseudocode
  - Time and space complexity analysis where applicable
5.4 Theoretical Analysis
  - Why the approach is expected to work
  - Any theoretical guarantees, bounds, or properties
5.5 Implementation Details
  - Key hyperparameters and their default values
  - Training procedure if applicable
  - Computational requirements

**6. Experimental Setup** (600–800 words)
6.1 Datasets
  - Describe 2–4 relevant benchmark datasets (or propose appropriate ones)
  - Dataset statistics: size, splits, characteristics
6.2 Baselines
  - List 4–6 competitive baseline methods
  - Brief description of each and why it is a fair comparison
6.3 Evaluation Metrics
  - Define each metric used and justify its relevance
6.4 Implementation
  - Framework, hardware, training details
  - Reproducibility considerations

**7. Expected Results & Analysis** (700–900 words)
7.1 Main Results
  - Describe expected quantitative results vs. baselines (use a placeholder table format)
  - Explain what the numbers would show and why
7.2 Ablation Study
  - Which components of the method are most important and why
  - Expected outcome of removing each component
7.3 Qualitative Analysis
  - Illustrative examples showing success and failure cases
  - What the model learns vs. what it misses
7.4 Computational Efficiency
  - Training and inference time compared to baselines

**8. Discussion** (500–600 words)
8.1 Implications
  - What does solving this gap mean for the field?
  - How does it change what is possible?
8.2 Limitations
  - Honest assessment of what the proposed approach cannot do
  - Scenarios where it would fail or underperform
8.3 Broader Impact
  - Positive societal implications
  - Potential risks or misuse scenarios
  - Ethical considerations

**9. Conclusion** (300–400 words)
- Concise restatement of the problem and gap
- Summary of the proposed approach
- Summary of key contributions
- 4–6 concrete future work directions, each with a brief justification

**References**
List 15–20 references in this exact format:
[N] LastName, F., LastName, F., and LastName, F. (Year). "Paper Title." In Proceedings of Conference / Journal Name, pages X–Y.

Make references plausible and consistent with the topic. Draw from the related work summary where possible.

---

Write in formal, precise academic English throughout. Every section must be complete and substantive — do not write placeholder text like "[insert result here]" except inside the results table. The paper should read as a genuine, thorough academic contribution."""


# ── Paper writer via CrewAI ───────────────────────────────────────────────────

def write_paper(topic: str, gap: str, related_work: str) -> str:
    llm        = get_llm("PAPER_WRITER")
    cloud_mode = is_cloud_provider("PAPER_WRITER")

    if cloud_mode:
        print("  Mode: FULL PAPER (cloud model — targeting 12-15 pages)", flush=True)
        prompt          = _cloud_prompt(topic, gap, related_work)
        expected_output = (
            "A complete 12-15 page academic research paper with Title, Authors, Abstract, "
            "Keywords, and 9 numbered sections plus References."
        )
    else:
        print("  Mode: DRAFT (local model — compact outline)", flush=True)
        prompt          = _local_prompt(topic, gap, related_work)
        expected_output = "A concise research paper draft with Title, Abstract, and 6 numbered sections."

    writer = Agent(
        role="AI Research Paper Author",
        goal="Write a rigorous, well-structured research paper that addresses an identified research gap",
        backstory=(
            "You are an expert AI researcher with a strong publication record at top venues "
            "(NeurIPS, ICML, ACL, ICCV). You write clearly, precisely, and with academic rigour. "
            "You always write in English and never truncate your response."
        ),
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=prompt,
        expected_output=expected_output,
        agent=writer,
    )

    crew   = Crew(agents=[writer], tasks=[task], verbose=False)
    result = crew.kickoff()
    return str(result)

# ── Resolve gap description for the current topic ─────────────────────────────

def _resolve_gap(topic: str) -> str:
    if not GAP_FILE.exists():
        return ""
    try:
        data = json.loads(GAP_FILE.read_text())
        for g in data.get("gaps", []):
            g_topic = g.get("topic", "").lower()
            if g_topic and (g_topic in topic.lower() or topic.lower() in g_topic):
                return g.get("gap", "")
        gaps = data.get("gaps", [])
        return gaps[0].get("gap", "") if gaps else ""
    except Exception:
        return ""

# ── Main agent function ────────────────────────────────────────────────────────

def write_research_paper() -> dict:
    print("Agent 4 (Research Mode): Writing research paper...", flush=True)

    synth_data    = json.loads(SYNTH_FILE.read_text())
    final_summary = synth_data.get("final_summary", "")
    topic         = synth_data.get("topic", "")

    if not topic and ANALYST_FILE.exists():
        topic = json.loads(ANALYST_FILE.read_text()).get("topic", "")

    gap = _resolve_gap(topic)

    print(f"  Topic : {topic}", flush=True)
    print(f"  Gap   : {gap}", flush=True)

    paper = write_paper(topic, gap, final_summary)

    print("\n" + "=" * 60, flush=True)
    print("RESEARCH PAPER", flush=True)
    print("=" * 60, flush=True)
    print(paper, flush=True)
    print("=" * 60 + "\n", flush=True)

    results = {
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "mode":          "research",
        "cloud":         is_cloud_provider("PAPER_WRITER"),
        "topic":         topic,
        "gap":           gap,
        "final_article": paper,
        "status":        "displayed",
    }

    OUTPUT_FILE.write_text(json.dumps(results, indent=2))
    print("Agent 4: Done! Research paper written.", flush=True)
    return results


if __name__ == "__main__":
    write_research_paper()
