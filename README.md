# 🤖 PulseAI — Latest AI Updates Pipeline

A multi-agent system that automatically fetches, organizes, summarizes, and publishes the latest AI developments — running entirely on **local models** via **CrewAI + Ollama**. No cloud AI API keys required.

---

## How It Works

```
Web Sources (DuckDuckGo)
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 1: Researcher                                            │
│  Searches the web via DuckDuckGo across configured AI sources   │
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
│  → Sends the summary via Email (Gmail)                          │
│  → Posts to LinkedIn                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
PulseAI/
├── backend/
│   ├── agents/
│   │   ├── researcher_agent.py   # DuckDuckGo search + Ollama curation
│   │   ├── analyst_agent.py      # CrewAI + Ollama 8-section report
│   │   ├── synthesizer_agent.py  # 5 local Ollama models + consolidation
│   │   ├── publisher_agent.py    # Email (smtplib) + LinkedIn API
│   │   └── trend_agent.py        # DuckDuckGo + Ollama trend detection
│   ├── config/
│   │   ├── sources.py            # Search sources (uncomment to add more)
│   │   └── tokens.py             # Ollama context/token limits
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

# ── Email via Gmail (optional — Agent 4) ─────────────────────────
# Use a Gmail App Password, NOT your account password.
# Enable at: myaccount.google.com → Security → App Passwords
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_gmail_app_password
EMAIL_TO=recipient@example.com

# ── LinkedIn (optional — Agent 4) ────────────────────────────────
# See the LinkedIn Setup section below.
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
LINKEDIN_PERSON_ID=your_linkedin_person_id
```

> **Note:** Email and LinkedIn are optional. If their keys are not set, Agent 4 skips those steps gracefully.

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
| `test_researcher_agent.py` | 9 | DDG search, article curation, topic injection, JSON fallback, file output |
| `test_analyst_agent.py` | 6 | Report schema, article count, file output, missing input error |
| `test_synthesizer_agent.py` | 13 | Ollama HTTP calls, per-model success/error, final consolidation, model counts |
| `test_publisher_agent.py` | 12 | LinkedIn post formatting, SMTP email, API calls, env var gating, error handling |
| `test_trend_agent.py` | 9 | DDG search, topic extraction, quote stripping, empty results, file output |
| `test_integration.py` | 8 | Full pipeline sequence, inter-agent data flow, output schemas, topic arg, credentials, dependency chain |

---

## Configuring Sources

By default, 3 sources are active. Open [backend/config/sources.py](backend/config/sources.py) and uncomment any sources you want to add:

```python
SOURCES = {
    "research": [
        # {"query": "site:arxiv.org/abs AI machine learning 2026", "label": "ArXiv"},
    ],
    "lab_blogs": [
        {"query": "Anthropic research latest AI 2026",  "label": "Anthropic Research"},  # ✅ active
        {"query": "OpenAI blog latest news 2026",       "label": "OpenAI Blog"},          # ✅ active
        {"query": "Google DeepMind research 2026",      "label": "Google DeepMind"},      # ✅ active
        # {"query": "Meta AI blog latest 2026",         "label": "Meta AI Blog"},
        ...
    ],
    ...
}
```

Each active source triggers one DuckDuckGo search call.

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

## LinkedIn Setup

LinkedIn requires a one-time OAuth 2.0 setup:

1. Go to the [LinkedIn Developer Portal](https://www.linkedin.com/developers/) and create an app
2. Add the `w_member_social` and `r_liteprofile` OAuth scopes
3. Use the **OAuth 2.0 tools** tab in the portal to generate an access token
4. Find your Person ID:
   ```bash
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        https://api.linkedin.com/v2/me
   ```
   The `id` field in the response is your `LINKEDIN_PERSON_ID`
5. Add both values to `PulseAI/.env`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent framework | Python + CrewAI |
| Local LLMs | Ollama (llama3.2, mistral, qwen2.5, phi3, gemma2) |
| Web search | DuckDuckGo (no API key required) |
| Dashboard | Streamlit (managed with uv) |
| Email | Python smtplib (Gmail) |
| Social | LinkedIn UGC Posts API v2 |
