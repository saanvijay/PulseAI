# 🤖 PulseAI — Latest AI Updates Pipeline

A multi-agent system that automatically fetches, organizes, summarizes, and displays a ready-to-publish article on the latest AI developments — running entirely on **local models** via **CrewAI + Ollama**. No cloud AI API keys required.

---

## How It Works

```
Web Sources (Google News RSS)
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 1: Researcher                                            │
│  Searches the web via Google News RSS across configured sources │
│  → Ollama organizes results into structured articles JSON       │
└───────────────────────────┬─────────────────────────────────────┘
                            │ researcher_output.json
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 2: Analyst                                               │
│  CrewAI + Ollama reads the articles                             │
│  → Produces a structured 8-section technical report            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ analyst_output.json
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 3: Synthesizer                                           │
│  Sends the report to 5 local Ollama models:                     │
│    Llama 3.2  ·  Mistral  ·  Qwen 2.5  ·  Phi-3  ·  Gemma 2   │
│  → Ollama consolidates all responses into one final summary     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ synthesizer_output.json
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 4: Publisher                                             │
│  → Displays the final article                                   │
│  → Ready to publish on LinkedIn, Medium, or any blog           │
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
│   │   ├── researcher_agent.py   # Google News RSS + Ollama curation
│   │   ├── analyst_agent.py      # CrewAI + Ollama 8-section report
│   │   ├── synthesizer_agent.py  # 5 local Ollama models + consolidation
│   │   ├── publisher_agent.py    # Displays the final article
│   │   └── trend_agent.py        # Google News RSS + Ollama trend detection
│   ├── output/                   # JSON outputs (created at runtime, gitignored)
│   ├── tests/
│   │   ├── conftest.py           # Shared pytest fixtures
│   │   ├── test_researcher_agent.py
│   │   ├── test_analyst_agent.py
│   │   ├── test_synthesizer_agent.py
│   │   ├── test_publisher_agent.py
│   │   ├── test_trend_agent.py
│   │   └── test_integration.py   # Full pipeline integration test
│   └── orchestrator.py           # Runs all agents in sequence
├── frontend/
│   ├── app.py                    # Streamlit dashboard
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

Install all dependencies (Streamlit + CrewAI + tools):

```bash
cd frontend && uv sync
```

### 3. Configure environment variables

Create your `.env` file in the project root (`PulseAI/.env`):

```bash
touch PulseAI/.env
```

Open `.env` and add the following:

```env
# ── Ollama (local — no API key needed) ────────────────────────────
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Running

### Option A — Streamlit Dashboard (recommended)

```bash
cd PulseAI/frontend
uv sync          # install dependencies first (only needed once)
uv run streamlit run app.py
```

The dashboard gives you:
- A **Run Full Pipeline** button to execute all 4 agents in sequence
- Individual buttons to run each agent separately
- A **Trend Agent** button to auto-detect the most trending AI topic
- Live log window streaming agent output in real time
- Collapsible panels showing each agent's output

### Option B — Command Line

```bash
cd backend

# Run the full pipeline (optional topic argument)
python orchestrator.py
python orchestrator.py "LLM reasoning and planning"

# Run individual agents
python agents/researcher_agent.py
python agents/researcher_agent.py "multimodal models"
python agents/analyst_agent.py
python agents/synthesizer_agent.py
python agents/publisher_agent.py

# Auto-detect trending topic
python agents/trend_agent.py
```

---

## Testing

The test suite covers every agent with mock unit tests and a full pipeline integration test. No Ollama server or internet connection is required — all external calls (DuckDuckGo, Ollama, Gmail, LinkedIn) are mocked.

### Install test dependency

```bash
cd frontend
uv add --dev pytest
```

### Run all tests

```bash
cd frontend
uv run pytest ../backend/tests/ -v
```

Expected output: **63 tests passing** in under 2 seconds.

### Run tests for a specific agent

```bash
uv run pytest ../backend/tests/test_researcher_agent.py -v
uv run pytest ../backend/tests/test_analyst_agent.py -v
uv run pytest ../backend/tests/test_synthesizer_agent.py -v
uv run pytest ../backend/tests/test_publisher_agent.py -v
uv run pytest ../backend/tests/test_trend_agent.py -v
```

### Run only the integration test

```bash
uv run pytest ../backend/tests/test_integration.py -v
```

### What is tested

| File | Tests | Coverage |
|------|-------|----------|
| `test_researcher_agent.py` | 9 | Google News search, article curation, topic injection, JSON fallback, file output |
| `test_analyst_agent.py` | 6 | Report schema, article count, file output, missing input error |
| `test_synthesizer_agent.py` | 13 | Ollama HTTP calls, per-model success/error, final consolidation, model counts |
| `test_publisher_agent.py` | 12 | Article display, output file writing, result structure |
| `test_trend_agent.py` | 9 | Google News search, topic extraction, quote stripping, empty results, file output |
| `test_integration.py` | 8 | Full pipeline sequence, inter-agent data flow, output schemas, topic arg, credentials, dependency chain |

---

## Configuring Sources

Open [config/sources.json](config/sources.json) and set `"enabled": true` for any sources you want to activate. By default, 3 sources are enabled:

```json
{
  "lab_blogs": [
    {"query": "Anthropic research latest AI 2026", "label": "Anthropic Research", "enabled": true},
    {"query": "OpenAI blog latest news 2026",      "label": "OpenAI Blog",        "enabled": true},
    {"query": "Google DeepMind research 2026",     "label": "Google DeepMind",    "enabled": true},
    {"query": "Meta AI blog latest 2026",          "label": "Meta AI Blog",       "enabled": false},
    ...
  ],
  "research": [
    {"query": "site:arxiv.org/abs AI machine learning 2026", "label": "ArXiv", "enabled": false},
    ...
  ]
}
```

Each enabled source triggers one Google News RSS fetch. To adjust token/context limits per agent, edit [config/tokens.json](config/tokens.json).

---

## Synthesizer Models

Agent 3 queries these Ollama models and consolidates their responses:

| Model | Pull command | Required? |
|-------|-------------|-----------|
| Llama 3.2 | `ollama pull llama3.2` | ✅ Yes (also used as primary) |
| Mistral | `ollama pull mistral` | Optional |
| Qwen 2.5 | `ollama pull qwen2.5` | Optional |
| Phi-3 | `ollama pull phi3` | Optional |
| Gemma 2 | `ollama pull gemma2` | Optional |

To change the primary model, set `OLLAMA_MODEL=<model>` in your `.env`. To add or remove models from the synthesizer, edit `OLLAMA_MODELS` in [backend/agents/synthesizer_agent.py](backend/agents/synthesizer_agent.py).

---

## Report Sections (Agent 2 Output)

Agent 2 uses Ollama to structure raw articles into a standardized 8-section report:

| # | Section | What it covers |
|---|---------|----------------|
| 1 | **Introduction** | Overview of latest trends and why they matter |
| 2 | **Existing Problems** | Challenges that motivated new developments |
| 3 | **Proposed Solutions** | New approaches, models, or methods introduced |
| 4 | **Architecture Overview** | ASCII diagram of how the systems work |
| 5 | **Advantages** | Benefits and improvements brought by the new work |
| 6 | **Disadvantages** | Limitations, risks, and open problems |
| 7 | **Applied AI Use Cases** | Real-world applications and industries impacted |
| 8 | **Future Implementation** | Upcoming milestones and predictions |

---

## Publishing the Article

Agent 4 outputs a polished article to the console and saves it to `backend/output/publisher_output.json`. You can use this article to:

- **LinkedIn** — copy and paste into a new LinkedIn post
- **Medium / Substack / Dev.to** — paste directly as a blog post
- **Email newsletter** — drop into your preferred email tool
- **Any other platform** — the article is plain text, ready to go anywhere

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent framework | Python + CrewAI |
| Local LLMs | Ollama (llama3.2, mistral, qwen2.5, phi3, gemma2) |
| Web search | Google News RSS (no API key required) |
| Dashboard | Streamlit (managed with uv) |
| Output | Plain-text article (publish anywhere) |
