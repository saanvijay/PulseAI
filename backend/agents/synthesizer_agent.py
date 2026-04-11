# Agent 3: Send the report to multiple local Ollama models and create a
# final consolidated summary using CrewAI + Ollama.
#
# Models tried (install via: ollama pull <model>):
#   llama3.2, mistral, qwen2.5, phi3, gemma2
# Any models not available locally are skipped gracefully.

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from crewai import Agent, Crew, LLM, Task
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

INPUT_FILE  = BASE_DIR / "output" / "analyst_output.json"
OUTPUT_FILE = BASE_DIR / "output" / "synthesizer_output.json"

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
PRIMARY_MODEL   = os.getenv("OLLAMA_MODEL", "llama3.2")

TOKENS = json.loads((BASE_DIR.parent / "config" / "tokens.json").read_text())

# Models to query in parallel — add/remove based on what you have pulled locally
OLLAMA_MODELS = [
    {"name": "Llama 3.2",  "model": "llama3.2"},
    {"name": "Mistral",    "model": "mistral"},
    {"name": "Qwen 2.5",   "model": "qwen2.5"},
    {"name": "Phi-3",      "model": "phi3"},
    {"name": "Gemma 2",    "model": "gemma2"},
]

# ── Ollama direct API call ─────────────────────────────────────────────────────

def ask_ollama(model: str, prompt: str, max_tokens: int = 1024) -> str:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model":   model,
            "prompt":  prompt,
            "stream":  False,
            "options": {"num_predict": max_tokens},
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()["response"]

# ── Per-model call with error handling ────────────────────────────────────────

def call_model(name: str, model: str, report: str) -> dict:
    try:
        print(f"  Asking {name}...")
        prompt = (
            "IMPORTANT: Respond in English only. Do not use any other language.\n\n"
            "You are an expert AI research analyst. Analyse the following AI report in depth and provide:\n\n"
            "1. **Key Developments** — The most significant breakthroughs or announcements and why they matter\n"
            "2. **Technical Insights** — Notable technical details, architectural choices, or methodology advances\n"
            "3. **Industry Impact** — How these developments affect companies, researchers, and end users\n"
            "4. **Risks & Limitations** — Concerns, open problems, or caveats raised\n"
            "5. **What to Watch** — The most important trends or follow-up areas to monitor\n\n"
            "Be specific and detailed. Reference actual models, papers, or companies from the report where relevant.\n\n"
            f"REPORT:\n{report}"
        )
        summary = ask_ollama(model, prompt, TOKENS["synthesizer_per_model"])
        return {"model": name, "status": "success", "summary": summary}
    except Exception as e:
        print(f"  {name} failed: {e}")
        return {"model": name, "status": "error", "error": str(e), "summary": None}

# ── Consolidation via CrewAI + Ollama ─────────────────────────────────────────

def create_final_summary(report: str, model_responses: list[dict]) -> str:
    successful    = [r for r in model_responses if r["status"] == "success"]
    responses_text = "\n\n---\n\n".join(
        f"[{r['model']}]:\n{r['summary']}" for r in successful
    )

    llm = LLM(model=f"ollama/{PRIMARY_MODEL}", base_url=OLLAMA_BASE_URL)

    consolidator = Agent(
        role="AI Insights Synthesizer",
        goal="Produce one definitive summary by combining insights from multiple AI model summaries",
        backstory=(
            "You are an expert at distilling complex AI research into clear, "
            "professional summaries suitable for publication on LinkedIn. You ALWAYS write in English only."
        ),
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""IMPORTANT: Respond in English only. Do not use any other language.

You have received in-depth analyses of an AI report from {len(successful)} different AI models.
Your task is to produce ONE comprehensive, well-structured final summary that synthesises the best insights from all of them.

ORIGINAL REPORT:
{report}

MODEL ANALYSES:
{responses_text}

Write a final summary structured with these sections:

## Overview
2-3 sentences capturing the overall theme and significance of this week's AI developments.

## Key Breakthroughs
The most important advances — be specific about models, companies, benchmarks, or papers mentioned.

## Technical Deep-Dive
The most interesting technical details, architectural choices, or methodological innovations.

## Industry & Business Impact
How these developments affect the AI industry, enterprises adopting AI, and the competitive landscape.

## Risks, Limitations & Open Questions
Honest assessment of what's missing, what could go wrong, and unsolved problems.

## What to Watch Next
The 3-5 most important things to follow up on in the coming weeks.

Guidelines:
- Be specific — name models, companies, researchers, and numbers from the report
- Aim for 600-800 words total
- Use bullet points within sections where appropriate
- Professional but accessible tone, suitable for a technical LinkedIn audience

Return only the structured summary with no meta-commentary.""",
        expected_output="A 600-800 word structured summary with 6 clearly marked sections.",
        agent=consolidator,
    )

    crew   = Crew(agents=[consolidator], tasks=[task], verbose=False)
    result = crew.kickoff()
    return str(result)

# ── Main agent function ────────────────────────────────────────────────────────

def summarize_with_multiple_models() -> dict:
    print("Agent 3: Getting summaries from multiple Ollama models...")

    input_data = json.loads(INPUT_FILE.read_text())
    report     = input_data["report"]

    # Call each model sequentially (Ollama is local — parallel adds no benefit)
    model_responses = [
        call_model(m["name"], m["model"], report)
        for m in OLLAMA_MODELS
    ]

    success_count = sum(1 for r in model_responses if r["status"] == "success")
    print(f"  {success_count}/{len(OLLAMA_MODELS)} models responded successfully.")

    print("  Creating final consolidated summary...")
    final_summary = create_final_summary(report, model_responses)

    output = {
        "timestamp":        datetime.now(timezone.utc).isoformat(),
        "models_queried":   len(OLLAMA_MODELS),
        "models_successful": success_count,
        "model_responses":  model_responses,
        "final_summary":    final_summary,
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print("Agent 3: Done! Final summary created from all model responses.")
    return output


if __name__ == "__main__":
    summarize_with_multiple_models()
