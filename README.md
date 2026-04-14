# 🤖 PulseAI — AI Research & Content Pipeline

[![CI](https://github.com/saanvijay/PulseAI/actions/workflows/ci.yml/badge.svg)](https://github.com/saanvijay/PulseAI/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

PulseAI is a **multi-agent AI pipeline** that turns any topic into a ready-to-publish article or a structured research paper draft — running entirely on **local models** via **CrewAI + Ollama**, with optional cloud model support for higher quality output.

It covers two distinct workflows:

- **Article mode** — fetches live AI news, analyzes it with multiple LLMs in parallel, and produces a blog-ready article on any topic you choose (manual, trending, or AI-suggested)
- **Research Paper mode** — discovers genuine unexplored research gaps from recent academic papers, then writes a structured paper draft addressing the selected gap (compact outline with local models, full 12–15 page academic paper with cloud models)

No cloud API keys required to get started. Everything runs locally by default.

---

## Two Modes

| Mode | Topic source | Output |
|------|-------------|--------|
| **Article** | Manual input or Trend Agent (live AI news) | Blog post / LinkedIn article — ready to publish |
| **Research Paper** | Manual input or Research Gap Agent (scans recent papers) | Compact 6-section draft (local) or full 12–15 page academic paper (cloud) |

### Research Paper mode — what it does and what it doesn't

The Research Paper pipeline:
1. **Scans recent academic papers** across 5 AI/ML categories (cs.AI, cs.LG, cs.CL, cs.CV, stat.ML) — filtering by your topic if provided
2. **Identifies 5 genuine research gaps** using a randomly rotated analytical lens (scalability, theoretical limits, safety, efficiency, etc.) so results differ each run
3. You **select one gap** as the research direction
4. The pipeline runs Researcher → Analyst → Synthesizer on that topic, then **writes a structured paper draft**

> **This is a draft, not a finished paper.** The output gives you a structured starting point — a gap worth investigating, a proposed methodology, and a literature foundation. The actual experiments, validation, real results, and final writing are yours to do before submitting anywhere.

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
│  → Identifies 5 genuine research gaps with descriptions         │
│  User selects one gap topic                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ (topic + gap selected)
                            ▼
            [Same Agents 1 → 2 → 3 as above]
                            │ synthesizer_output.json
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 4: Paper Writer                                          │
│                                                                 │
│  LOCAL MODEL → compact draft (~2-3 pages, 6 sections)          │
│    Abstract · Introduction · Related Work · Problem Statement   │
│    Methodology · Discussion · Conclusion · References           │
│                                                                 │
│  CLOUD MODEL → full academic paper (~12-15 pages, 9 sections)  │
│    Abstract · Keywords · Introduction · Background              │
│    Related Work · Problem Formulation · Methodology             │
│    Experimental Setup · Results · Discussion · Conclusion       │
│    References (15-20 entries)                                   │
│                                                                 │
│  → A starting point — you do the real research & experiments    │
│  → Download as Markdown or plain text                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
PulseAI/
├── config/
│   ├── sources.json              # Search sources — set "enabled": true/false to toggle
│   └── tokens.json               # Token/context limits per agent
├── backend/
│   ├── llm_factory.py            # Resolves which LLM each agent uses (local or cloud)
│   ├── agents/
│   │   ├── researcher_agent.py   # Google News RSS + full-content scraping + retry logic
│   │   ├── analyst_agent.py      # CrewAI + LLM content-driven report
│   │   ├── synthesizer_agent.py  # 5 local Ollama models in parallel + LLM consolidation
│   │   ├── publisher_agent.py    # Displays final article
│   │   ├── paper_writer_agent.py # Draft (local) or full paper (cloud) in research mode
│   │   ├── trend_agent.py        # Google News RSS + LLM trend detection
│   │   └── research_gap_agent.py # Scans recent papers + LLM gap identification
│   ├── output/                   # JSON outputs (created at runtime, gitignored)
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_researcher_agent.py
│   │   ├── test_analyst_agent.py
│   │   ├── test_synthesizer_agent.py
│   │   ├── test_publisher_agent.py
│   │   ├── test_trend_agent.py
│   │   └── test_integration.py
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
| **🏠 Pipeline** | Topic selection, run buttons, live status indicators |
| **🔎 Researcher** | Fetched articles grouped by category (✦ = full content scraped) |
| **📋 Analyst** | Structured technical report |
| **🧠 Synthesizer** | Final consolidated summary + individual model responses |
| **📤 Publisher** | Final article or research paper with download buttons |
| **📡 Log** | Live streaming log with Stop button |

**Topic selection** has three inner tabs inside the Pipeline tab:

| Tab | How it works |
|-----|-------------|
| **✏️ Enter Manually** | Type any topic and set it directly |
| **🔍 Trending Topics** | Runs Trend Agent → pick from 5 live trending topics |
| **🔬 Research Gap** | Optional topic filter → Runs Research Gap Agent → pick a gap to research |

After selecting a topic from any tab, **both run buttons are always available**:

| Button | What it does |
|--------|-------------|
| **🚀 Run Full Pipeline → Article** | Researcher → Analyst → Synthesizer → Publisher (blog article) |
| **🔬 Run Research Pipeline → Paper** | Researcher → Analyst → Synthesizer → Paper Writer (research draft) |

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
- Generates **6–9 content-driven section headings** based on what themes emerge from the articles — no fixed template
- Each section references specific models, companies, and numbers
- Output: `analyst_output.json`

### Agent 3 — Synthesizer

- Queries all 5 Ollama models **in parallel** using `ThreadPoolExecutor` (up to 5x faster than sequential)
- Each model produces independent analysis: Key Developments, Technical Insights, Industry Impact, Risks, What to Watch
- Consolidates all successful responses into one **600–800 word final summary**
- Missing models are skipped gracefully; each call **retries** up to 3 times with backoff
- Output: `synthesizer_output.json`

### Agent 4a — Publisher *(Article mode)*

- Displays the final article and saves it
- Download as **Markdown** or **plain text**
- Ready to copy to LinkedIn, Medium, Substack, or any blog
- Output: `publisher_output.json`

### Agent 4b — Paper Writer *(Research mode)*

Output quality depends on the model configured for `PAPER_WRITER`:

| Model type | Output |
|-----------|--------|
| **Local model** (default) | Compact draft ~2–3 pages, 6 sections. Good for quickly exploring the idea. |
| **Cloud model** (optional) | Full academic paper ~12–15 pages (~6000–8000 words), 9 sections. Much more detailed and coherent. |

**Sections in cloud mode (full paper):**
1. Abstract (250–300 words) + Keywords
2. Introduction (700–900 words) — background, motivation, gap, contributions, paper organisation
3. Background & Preliminaries (400–600 words) — key concepts, notation, foundations
4. Related Work (900–1100 words) — 4–6 themed subsections, critical analysis of limitations
5. Problem Formulation (500–700 words) — formal definition, assumptions, evaluation criteria
6. Proposed Methodology (1200–1600 words) — architecture, algorithm/pseudocode, complexity, theoretical analysis
7. Experimental Setup (600–800 words) — datasets, baselines, metrics, implementation details
8. Expected Results & Analysis (700–900 words) — quantitative results, ablation study, qualitative analysis
9. Discussion (500–600 words) — implications, limitations, broader impact
10. Conclusion (300–400 words) — summary, future work
11. References — 15–20 plausible entries

> **This is a draft, not a finished paper.** The output gives you a structured idea and gap to investigate. You still need to conduct actual experiments, gather real results, validate your approach, and write the final paper yourself before submitting anywhere.

### Trend Agent *(Topic discovery — Article mode)*

- Scans all enabled Google News RSS sources in parallel
- Uses LLM to extract the **top 5 trending AI topic phrases**
- Falls back to inactive sources if too few headlines are found
- Output: `trend_output.json`

### Research Gap Agent *(Topic discovery — Research mode)*

- Fetches recent papers from **5 research categories** in parallel (cs.AI, cs.LG, cs.CL, cs.CV, stat.ML)
- **Topic-aware search** — uses your pipeline topic (or an explicit filter) to search paper abstracts and bodies (`all:` field), not just titles, so narrow topics still return results
- **Randomised each run** — uses a random start offset per category, shuffles and samples a different subset of papers, and rotates through 10 analytical lenses (scalability, safety, efficiency, interpretability, etc.) so you get genuinely different gaps every time you click Run
- Uses LLM at `temperature=0.9` to identify **5 genuine research gaps** with title + one-sentence gap description
- Selecting a gap automatically enables Research Paper mode for the pipeline
- Output: `research_gap_output.json`

---

## Cloud Models (Optional)

By default every agent runs on local Ollama models — no API keys, no cost. If you want higher quality output (especially for the Research Paper mode), you can switch any agent to a cloud model.

### How it works

`backend/llm_factory.py` resolves which model each agent uses, in this priority order:

| Priority | Env var | Scope |
|----------|---------|-------|
| 1 (highest) | `{AGENT}_MODEL` + `{AGENT}_PROVIDER` | Single agent override |
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

Keep everything else local and free. Only the paper writing step uses a cloud model:

```env
# All other agents stay on local Ollama
OLLAMA_MODEL=llama3.2

# Only the Paper Writer uses Claude
PAPER_WRITER_PROVIDER=anthropic
PAPER_WRITER_MODEL=claude-opus-4-6
ANTHROPIC_API_KEY=sk-ant-...
```

### Supported providers

| Provider | `_PROVIDER` value | Example models |
|----------|------------------|----------------|
| Ollama (local) | `ollama` | Any model pulled locally |
| Anthropic | `anthropic` | `claude-opus-4-6`, `claude-sonnet-4-6` |
| OpenAI | `openai` | `gpt-4o`, `gpt-4o-mini` |

### Paper Writer output by model

| Model | Pages | Words | Sections |
|-------|-------|-------|---------|
| Local (e.g. llama3.2) | ~2–3 | ~800–1200 | 6 |
| Cloud (e.g. Claude, GPT-4o) | ~12–15 | ~6000–8000 | 9 + references |

The Publisher tab shows a badge indicating which type was used (`☁️ cloud` or `💻 local`) so you always know what you got.

> Even with cloud models the output is a **draft** — real research, experiments, and validation are still yours to do before submitting anywhere.

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

- **Article mode** — ready to publish as-is on LinkedIn, Medium, Substack, Dev.to, or any blog
- **Research Paper mode** — a draft to build on. Conduct your own research, run experiments, and write the final paper before submitting anywhere

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent framework | Python + CrewAI |
| Local LLMs (default) | Ollama (llama3.2, mistral, qwen2.5, phi3, gemma2) |
| Cloud LLMs (optional) | Anthropic (Claude), OpenAI (GPT-4o) via `llm_factory.py` |
| LLM routing | `backend/llm_factory.py` — per-agent or global provider override |
| Web search | Google News RSS (no API key required) |
| Article scraping | BeautifulSoup4 |
| Research paper source | Academic paper APIs (cs.AI, cs.LG, cs.CL, cs.CV, stat.ML) |
| Dashboard | Streamlit (managed with uv) |
| Output | Plain-text article or research paper draft |
