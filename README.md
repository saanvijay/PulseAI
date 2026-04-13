# 🤖 PulseAI — Latest AI Updates Pipeline

A multi-agent system that automatically fetches, organizes, summarizes, and displays a ready-to-publish **article** or a **research paper draft** on the latest AI developments — running entirely on **local models** via **CrewAI + Ollama**. No cloud AI API keys required.

---

## Two Modes

| Mode | Topic source | Output |
|------|-------------|--------|
| **Article** | Trending topics or manual input | Blog post / LinkedIn article — ready to publish |
| **Research Paper** | Research Gap Agent (unexplored areas in recent papers) | A draft outline and idea — a starting point for your own real research |

> **Important:** The Research Paper mode does **not** produce a publication-ready paper. It identifies a potential research gap and generates a structured draft to help you get started. The actual research, experiments, validation, and writing are yours to do before submitting anywhere.

---

## How It Works

### Article Pipeline

```
Topic (manual / Trend Agent)
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 1: Researcher                                            │
│  Fetches articles via Google News RSS across configured sources │
│  Scrapes full content for top 10 articles (BeautifulSoup)       │
│  Retries failed fetches with exponential backoff                │
└───────────────────────────┬─────────────────────────────────────┘
                            │ researcher_output.json
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 2: Analyst                                               │
│  CrewAI + Ollama reads full article content                     │
│  → Produces a structured technical report (content-driven       │
│    headings, not a fixed template)                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ analyst_output.json
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 3: Synthesizer                                           │
│  Queries 5 local Ollama models IN PARALLEL:                     │
│    Llama 3.2  ·  Mistral  ·  Qwen 2.5  ·  Phi-3  ·  Gemma 2   │
│  → Consolidates all responses into one final summary            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ synthesizer_output.json
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 4: Publisher                                             │
│  → Displays the final article                                   │
│  → Download as Markdown or plain text                           │
│  → Ready to publish on LinkedIn, Medium, or any blog            │
└─────────────────────────────────────────────────────────────────┘
```

### Research Paper Pipeline

```
Research Gap Agent (optional broad area input)
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Research Gap Agent                                             │
│  Scans recent papers across 5 categories in parallel:           │
│    cs.AI  ·  cs.LG  ·  cs.CL  ·  cs.CV  ·  stat.ML            │
│  → Ollama identifies 5 genuine research gaps                    │
│  User selects one gap topic                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ (topic + gap selected)
                            ▼
            [Same Agents 1 → 2 → 3 as above]
                            │ synthesizer_output.json
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 4: Paper Writer                                          │
│  CrewAI + Ollama generates a draft research paper outline:      │
│    Abstract · Introduction · Related Work · Problem Statement   │
│    Methodology · Discussion · Conclusion · References           │
│  → A starting point — you do the real research & experiments    │
│  → Download as text or Markdown to continue in your own editor  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
PulseAI/
├── config/
│   ├── sources.json              # Search sources — set "enabled": true/false to toggle
│   └── tokens.json               # Ollama context/token limits per agent
├── backend/
│   ├── agents/
│   │   ├── researcher_agent.py   # Google News RSS + full-content scraping + retry logic
│   │   ├── analyst_agent.py      # CrewAI + Ollama content-driven report
│   │   ├── synthesizer_agent.py  # 5 local Ollama models queried in parallel + consolidation
│   │   ├── publisher_agent.py    # Displays final article
│   │   ├── paper_writer_agent.py # Writes structured research paper (research mode)
│   │   ├── trend_agent.py        # Google News RSS + Ollama trend detection
│   │   └── research_gap_agent.py # Scans recent papers + Ollama gap identification
│   ├── output/                   # JSON outputs (created at runtime, gitignored)
│   ├── tests/
│   │   ├── conftest.py           # Shared pytest fixtures
│   │   ├── test_researcher_agent.py
│   │   ├── test_analyst_agent.py
│   │   ├── test_synthesizer_agent.py
│   │   ├── test_publisher_agent.py
│   │   ├── test_trend_agent.py
│   │   └── test_integration.py   # Full pipeline integration test
│   └── orchestrator.py           # Runs all agents in sequence (article or research mode)
├── frontend/
│   ├── app.py                    # Streamlit dashboard (tab-based UI)
│   └── pyproject.toml            # Python dependencies (uv)
├── .env                          # Your configuration (gitignored)
├── .gitignore
└── README.md
```

---

## Setup

### 1. Install Ollama

Download and install Ollama from [ollama.com](https://ollama.com), then start the server:

```bash
ollama serve
```

Pull the primary model (required):

```bash
ollama pull llama3.2
```

Pull additional models for the Synthesizer agent (optional — skipped gracefully if missing):

```bash
ollama pull mistral
ollama pull qwen2.5
ollama pull phi3
ollama pull gemma2
```

### 2. Clone and install Python dependencies

```bash
git clone <your-repo-url>
cd PulseAI
```

Install [uv](https://github.com/astral-sh/uv) if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install all dependencies (Streamlit + CrewAI + BeautifulSoup + tools):

```bash
cd frontend && uv sync
```

### 3. Configure environment variables

Create your `.env` file in the project root (`PulseAI/.env`):

```env
# ── Ollama (local — no API key needed) ────────────────────────────
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434

# ── Cloud models (optional — see Cloud Models section below) ──────
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-opus-4-6
# ANTHROPIC_API_KEY=sk-ant-...
```

---

## Running

### Option A — Streamlit Dashboard (recommended)

```bash
cd PulseAI/frontend
uv sync          # install dependencies first (only needed once)
uv run streamlit run app.py
```

The dashboard is tab-based:

| Tab | Content |
|-----|---------|
| **🏠 Pipeline** | Topic selection, run buttons, status indicators |
| **🔎 Researcher** | Fetched articles grouped by category (✦ = full content scraped) |
| **📋 Analyst** | Structured technical report |
| **🧠 Synthesizer** | Final consolidated summary + individual model responses |
| **📤 Publisher** | Final article or research paper with download buttons |
| **📡 Log** | Live streaming log with Stop button |

**Topic selection** has three inner tabs in the Pipeline tab:

| Tab | How it works |
|-----|-------------|
| **✏️ Enter Manually** | Type any topic and set it directly |
| **🔍 Trending Topics** | Runs Trend Agent → pick from 5 live trending topics |
| **🔬 Research Gap** | Optional broad area → Runs Research Gap Agent → pick a gap topic → pipeline outputs a research paper |

### Option B — Command Line

```bash
cd backend

# Article pipeline (optional topic)
python orchestrator.py
python orchestrator.py "LLM reasoning and planning"

# Research paper pipeline
python orchestrator.py "topic" --research

# Run individual agents
python agents/researcher_agent.py
python agents/researcher_agent.py "multimodal models"
python agents/analyst_agent.py
python agents/synthesizer_agent.py
python agents/publisher_agent.py
python agents/paper_writer_agent.py

# Topic discovery agents
python agents/trend_agent.py
python agents/research_gap_agent.py
python agents/research_gap_agent.py "computer vision"
```

---

## Agents

### Agent 1 — Researcher

- Fetches articles from Google News RSS across all configured sources in **parallel batches**
- Automatically falls back to research sources if primary sources return too few results
- **Scrapes full article content** for the top 10 results using BeautifulSoup (removes nav/footer noise, extracts up to 3000 chars of main text)
- **Retries** failed fetches up to 3 times with exponential backoff
- Deduplicates by URL
- Output: `researcher_output.json`

### Agent 2 — Analyst

- Uses **full scraped content** when available (falls back to RSS snippet)
- Generates **6–9 content-driven section headings** based on what themes actually emerge from the articles — no fixed template
- Each section includes specific references to models, companies, and numbers
- Output: `analyst_output.json`

### Agent 3 — Synthesizer

- Queries all 5 Ollama models **in parallel** using `ThreadPoolExecutor` (up to 5x faster than sequential)
- Each model produces independent analysis across 5 dimensions: Key Developments, Technical Insights, Industry Impact, Risks, What to Watch
- CrewAI consolidates all successful responses into one **600–800 word final summary**
- Missing models are skipped gracefully
- **Retries** each Ollama call up to 3 times with backoff
- Output: `synthesizer_output.json`

### Agent 4a — Publisher *(Article mode)*

- Displays the final article to the console and saves it
- Download as **Markdown** or **plain text**
- Ready to copy to LinkedIn, Medium, Substack, or any blog
- Output: `publisher_output.json`

### Agent 4b — Paper Writer *(Research mode)*

- Takes the synthesizer summary + selected research gap
- Uses CrewAI + Ollama to generate a **structured draft outline**:
  - Title, Abstract (150–250 words)
  - Introduction with numbered contributions
  - Related Work (grounded in the synthesizer summary)
  - Problem Statement
  - Proposed Methodology
  - Discussion
  - Conclusion
  - References (6–10 entries)
- Download as **Markdown** or **plain text**
- Output: `publisher_output.json` with `"mode": "research"`

> **This is a starting point, not a finished paper.** The output gives you a structured idea and a gap to investigate — you still need to conduct actual experiments, gather real results, validate your approach, and write the final paper yourself before submitting to any platform or journal.

### Trend Agent *(Topic discovery)*

- Scans all enabled Google News RSS sources in parallel
- Uses Ollama to extract the **top 5 trending AI topic phrases**
- Falls back to inactive sources if too few headlines are found
- Output: `trend_output.json`

### Research Gap Agent *(Topic discovery — Research mode)*

- Fetches recent papers from **5 research categories** in parallel (cs.AI, cs.LG, cs.CL, cs.CV, stat.ML)
- Accepts an optional broad area to narrow the search (e.g. "computer vision")
- Uses CrewAI + Ollama to identify **5 genuine research gaps** with title + gap description
- Selecting a gap automatically enables Research Paper mode in the UI
- Output: `research_gap_output.json`

---

## Testing

The test suite covers every agent with mock unit tests and a full pipeline integration test. No Ollama server or internet connection required.

### Run all tests

```bash
cd frontend
uv run pytest ../backend/tests/ -v
```

### Run tests for a specific agent

```bash
uv run pytest ../backend/tests/test_researcher_agent.py -v
uv run pytest ../backend/tests/test_analyst_agent.py -v
uv run pytest ../backend/tests/test_synthesizer_agent.py -v
uv run pytest ../backend/tests/test_publisher_agent.py -v
uv run pytest ../backend/tests/test_trend_agent.py -v
uv run pytest ../backend/tests/test_integration.py -v
```

### What is tested

| File | Coverage |
|------|----------|
| `test_researcher_agent.py` | Google News search, full-content scraping, retry logic, topic injection, fallback sources, deduplication, file output |
| `test_analyst_agent.py` | Report schema, full-content vs snippet usage, article count, file output |
| `test_synthesizer_agent.py` | Parallel Ollama calls, per-model success/error, retry logic, consolidation, model counts |
| `test_publisher_agent.py` | Article display, output file writing, result structure |
| `test_trend_agent.py` | Google News search, topic extraction, quote stripping, empty results, file output |
| `test_integration.py` | Full pipeline sequence, inter-agent data flow, output schemas, topic arg, dependency chain |

---

## Configuring Sources

Open [config/sources.json](config/sources.json) and set `"enabled": true` for any sources you want to activate. The `enabled` flag controls which sources the **Trend Agent** scans. The **Researcher Agent** uses all sources regardless of this flag.

```json
{
  "lab_blogs": [
    {"query": "Anthropic research latest AI 2026", "label": "Anthropic Research", "enabled": true},
    {"query": "OpenAI blog latest news 2026",      "label": "OpenAI Blog",        "enabled": true},
    {"query": "Google DeepMind research 2026",     "label": "Google DeepMind",    "enabled": true},
    {"query": "Meta AI blog latest 2026",          "label": "Meta AI Blog",       "enabled": false}
  ],
  "research": [
    {"query": "site:arxiv.org/abs AI machine learning 2026", "label": "Research Papers", "enabled": false}
  ]
}
```

To adjust token/context limits per agent, edit [config/tokens.json](config/tokens.json).

---

## Synthesizer Models

Agent 3 queries these Ollama models in parallel and consolidates their responses:

| Model | Pull command | Required? |
|-------|-------------|-----------|
| Llama 3.2 | `ollama pull llama3.2` | ✅ Yes (also used as primary) |
| Mistral | `ollama pull mistral` | Optional |
| Qwen 2.5 | `ollama pull qwen2.5` | Optional |
| Phi-3 | `ollama pull phi3` | Optional |
| Gemma 2 | `ollama pull gemma2` | Optional |

To change the primary model, set `OLLAMA_MODEL=<model>` in your `.env`. To add or remove models from the synthesizer, edit `OLLAMA_MODELS` in [backend/agents/synthesizer_agent.py](backend/agents/synthesizer_agent.py).

---

## Output

| Mode | Output file | Download formats |
|------|-------------|-----------------|
| Article | `backend/output/publisher_output.json` | Markdown, plain text |
| Research Paper | `backend/output/publisher_output.json` | Markdown, plain text |

The output is always plain text — copy it to any platform:

- **Article mode**: LinkedIn, Medium, Substack, Dev.to, email newsletter — ready to publish as-is
- **Research Paper mode**: a draft idea and structure to build on — conduct your own research, run experiments, and write the real paper before submitting to any platform or journal

---

## Cloud Models (Optional)

By default every agent runs on local Ollama models — no API keys, no cost. If you want higher quality output (especially for the Research Paper mode), you can optionally switch any agent to a cloud model.

### How it works

A central `llm_factory.py` resolves which model each agent uses, in this priority order:

| Priority | Env var | Example |
|----------|---------|---------|
| 1 (highest) | `{AGENT}_MODEL` + `{AGENT}_PROVIDER` | Per-agent override |
| 2 | `LLM_MODEL` + `LLM_PROVIDER` | All agents at once |
| 3 (default) | `OLLAMA_MODEL` + `OLLAMA_BASE_URL` | Local Ollama |

Agent keys: `ANALYST`, `SYNTHESIZER`, `PAPER_WRITER`, `TREND`, `RESEARCH_GAP`

### Option A — Upgrade all agents to a cloud model

```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-opus-4-6
ANTHROPIC_API_KEY=sk-ant-...
```

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

### Option B — Upgrade only the Paper Writer (recommended)

Keep everything local but use a cloud model just for writing the research paper draft, where output quality matters most:

```env
# All other agents stay on local Ollama
OLLAMA_MODEL=llama3.2

# Only the Paper Writer uses Claude
PAPER_WRITER_PROVIDER=anthropic
PAPER_WRITER_MODEL=claude-opus-4-6
ANTHROPIC_API_KEY=sk-ant-...
```

### Supported providers

| Provider | `_PROVIDER` value | Models |
|----------|------------------|--------|
| Ollama (local) | `ollama` | Any model pulled locally |
| Anthropic | `anthropic` | `claude-opus-4-6`, `claude-sonnet-4-6`, etc. |
| OpenAI | `openai` | `gpt-4o`, `gpt-4o-mini`, etc. |

> **Paper length by model type:**
> - **Local model** → compact draft (~2-3 pages, 6 sections). Local 7B models struggle with long coherent outputs.
> - **Cloud model** → full academic paper (~12-15 pages, 9 sections + references, ~6000-8000 words): Abstract, Keywords, Introduction, Background & Preliminaries, Related Work, Problem Formulation, Methodology, Experimental Setup, Expected Results, Discussion, Conclusion, References.
>
> Even with cloud models the output is a **draft** — real research, experiments, and validation are still yours to do before submitting anywhere.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent framework | Python + CrewAI |
| Local LLMs (default) | Ollama (llama3.2, mistral, qwen2.5, phi3, gemma2) |
| Cloud LLMs (optional) | Anthropic (Claude), OpenAI (GPT-4o) via `llm_factory.py` |
| Web search | Google News RSS (no API key required) |
| Article scraping | BeautifulSoup4 |
| Research paper source | Academic paper APIs (cs.AI, cs.LG, cs.CL, cs.CV, stat.ML categories) |
| Dashboard | Streamlit (managed with uv) |
| Output | Plain-text article or research paper draft |
