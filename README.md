# 🤖 PulseAI — Latest AI Updates Pipeline

A multi-agent system that automatically fetches, organizes, summarizes, and publishes the latest AI developments. Each agent is a focused, single-responsibility Node.js module orchestrated through a Streamlit dashboard.

---

## How It Works

```
Web Sources
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 1: Fetch                                                 │
│  Searches the web using Serper API across 4 AI-focused queries  │
│  → Collects titles, snippets, and links                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ agent1_output.json
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 2: Organize                                              │
│  Sends raw articles to Claude Opus 4.6                          │
│  → Produces a structured 8-section technical report            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ agent2_output.json
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 3: Summarize                                             │
│  Sends the report to 5 AI models in parallel:                   │
│    Claude Opus 4.6  ·  GPT-4o  ·  Gemini 1.5 Pro               │
│    Mistral Large    ·  Cohere Command R+                        │
│  → Claude consolidates all responses into one final summary     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ agent3_output.json
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent 4: Publish                                               │
│  → Sends the summary via Email (Gmail + Nodemailer)             │
│  → Posts to LinkedIn                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
PulseAI/
├── backend/
│   ├── agents/
│   │   ├── agent1_fetch.js       # Claude web search across 16 sources
│   │   ├── agent2_organize.js    # Structures content with Claude
│   │   ├── agent3_summarize.js   # 5 AI models via OpenRouter + final summary
│   │   └── agent4_publish.js     # Email + LinkedIn publishing
│   ├── output/                   # JSON outputs (created at runtime, gitignored)
│   ├── orchestrator.js           # Runs all agents in sequence
│   └── package.json
├── frontend/
│   ├── app.py                    # Streamlit dashboard
│   └── pyproject.toml            # Python dependencies (uv)
├── .env                          # Your API keys (gitignored)
├── .env.example                  # Template — copy to .env
├── .gitignore
└── README.md
```

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd PulseAI

# Node.js dependencies
cd backend && npm install && cd ..

# Python dependencies (using uv)
cd frontend && uv sync && cd ..
```

> **Install uv** if you don't have it: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your API keys:

```env
# AI Models
ANTHROPIC_API_KEY=your_anthropic_api_key      # platform.anthropic.com — Agent 1 (web search), Agent 2, Agent 3 (Claude)
OPENROUTER_API_KEY=your_openrouter_api_key    # openrouter.ai — Agent 3: GPT-4o, Gemini, Mistral, Cohere

# Email — use a Gmail App Password, NOT your account password
# Enable at: myaccount.google.com → Security → App Passwords
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_gmail_app_password
EMAIL_TO=recipient@example.com

# LinkedIn — see LinkedIn Setup section below
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
LINKEDIN_PERSON_ID=your_linkedin_person_id
```

> **Note:** Agent 3 requires all 5 AI model keys to get responses from all models. If a key is missing, that model will be skipped and the final summary will be based on the remaining responses.

> **Note:** Agent 4 email and LinkedIn are optional. If the keys are not set, those steps are skipped gracefully.

---

## Running

### Option A — Streamlit Dashboard (recommended)

```bash
cd frontend
uv run streamlit run app.py
```

The dashboard gives you:
- A **Run Full Pipeline** button to execute all 4 agents at once
- Individual buttons to run each agent separately
- Four tabs showing the output of each agent in real time

### Option B — Command Line

```bash
cd backend

# Run the full pipeline
node orchestrator.js

# Or run individual agents
node agents/agent1_fetch.js
node agents/agent2_organize.js
node agents/agent3_summarize.js
node agents/agent4_publish.js
```

---

## Report Sections (Agent 2 Output)

Agent 2 uses Claude to structure the raw articles into a standardized 8-section report:

| # | Section | What it covers |
|---|---------|---------------|
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

LinkedIn requires OAuth 2.0. Here is the one-time setup:

1. Go to the [LinkedIn Developer Portal](https://www.linkedin.com/developers/) and create an app
2. Add the `w_member_social` and `r_liteprofile` OAuth scopes
3. Use the **OAuth 2.0 tools** tab in the portal to generate an access token
4. Find your Person ID by calling:
   ```bash
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        https://api.linkedin.com/v2/me
   ```
   The `id` field in the response is your `LINKEDIN_PERSON_ID`
5. Add both values to your `.env` file

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent runtime | Node.js |
| Dashboard | Python + Streamlit (managed with uv) |
| Web search | Serper API |
| AI models | Claude Opus 4.6, GPT-4o, Gemini 1.5 Pro, Mistral Large, Cohere Command R+ |
| Email | Nodemailer (Gmail) |
| Social | LinkedIn UGC Posts API |

---

## API Keys Reference

| Key | Where to get it | Free tier |
|-----|----------------|-----------|
| `ANTHROPIC_API_KEY` | [platform.anthropic.com](https://platform.anthropic.com) | Pay-as-you-go |
| `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai) | Free tier available — covers GPT-4o, Gemini, Mistral, Cohere |
