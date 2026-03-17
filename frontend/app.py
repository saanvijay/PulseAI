"""
PulseAI - Streamlit Dashboard for the Multi-Agent AI Pipeline
"""

import json
import os
import subprocess
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PulseAI — Latest AI Updates",
    page_icon="🤖",
    layout="wide",
)

ROOT_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # PulseAI/
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
OUTPUT_DIR  = os.path.join(BACKEND_DIR, "output")


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(filename):
    """Read a JSON output file. Returns None if it doesn't exist yet."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        return json.load(f)


def run_node_script(script_path, topic=""):
    """Run a Node.js script and return exit code, stdout, stderr."""
    cmd = ["node", script_path]
    if topic:
        cmd.append(topic)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=BACKEND_DIR,
    )
    return result.returncode, result.stdout, result.stderr


def stream_researcher(topic=""):
    """Run the researcher agent and stream its output line by line into a log box."""
    cmd = ["node", os.path.join(BACKEND_DIR, "agents/researcher_agent.js")]
    if topic:
        cmd.append(topic)

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=BACKEND_DIR,
    )

    lines = []
    log_box = st.empty()

    for raw_line in iter(process.stdout.readline, ""):
        line = raw_line.rstrip()
        if line:
            lines.append(line)
            log_box.code("\n".join(lines), language="bash")

    process.stdout.close()
    process.wait()
    return process.returncode


def status_badge(status):
    if status == "success":
        return "✅ Success"
    elif status == "error":
        return "❌ Error"
    elif status == "skipped":
        return "⏭️ Skipped"
    return status


# ── Live log placeholder (defined early so it renders at top of main area) ────
# This is filled by the Researcher button handler with streaming output.
log_placeholder = st.empty()


# ── Sidebar ───────────────────────────────────────────────────────────────────

SUGGESTED_TOPICS = [
    "LLM Reasoning", "AI Agents", "Multimodal AI", "Computer Vision",
    "Robotics", "RAG", "Fine-tuning", "AI Safety",
]

if "topic" not in st.session_state:
    st.session_state.topic = ""

st.sidebar.title("🤖 PulseAI")
st.sidebar.markdown("Multi-agent pipeline for the latest AI updates.")
st.sidebar.divider()

st.sidebar.subheader("Research Topic")

topic_input = st.sidebar.text_input(
    "Topic",
    value=st.session_state.topic,
    placeholder="e.g. LLM agents, multimodal AI...",
    label_visibility="collapsed",
)
st.session_state.topic = topic_input

st.sidebar.caption("Suggestions — click to fill:")
sug_cols = st.sidebar.columns(2)
for i, sug in enumerate(SUGGESTED_TOPICS):
    if sug_cols[i % 2].button(sug, use_container_width=True):
        st.session_state.topic = sug
        st.rerun()

topic = st.session_state.topic
st.sidebar.divider()

st.sidebar.subheader("Run Agents")

if st.sidebar.button("🚀 Run Full Pipeline", use_container_width=True, type="primary"):
    with st.spinner("Running full pipeline (this takes a few minutes)..."):
        code, out, err = run_node_script(os.path.join(BACKEND_DIR, "orchestrator.js"), topic)
    if code == 0:
        st.sidebar.success("Pipeline complete!")
    else:
        st.sidebar.error(f"Pipeline failed:\n{err}")
    st.rerun()

st.sidebar.divider()

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Researcher", use_container_width=True):
        with log_placeholder.container():
            st.markdown("#### 📡 Researcher Agent — Live Log")
            code = stream_researcher(topic)
            if code == 0:
                st.success("Researcher done!")
            else:
                st.error("Researcher failed. See log above.")
        st.rerun()

    if st.button("Synthesizer", use_container_width=True):
        with st.spinner("Running Synthesizer Agent..."):
            code, out, err = run_node_script(os.path.join(BACKEND_DIR, "agents/synthesizer_agent.js"))
        st.sidebar.success("Done!") if code == 0 else st.sidebar.error(err)
        st.rerun()

with col2:
    if st.button("Analyst", use_container_width=True):
        with st.spinner("Running Analyst Agent..."):
            code, out, err = run_node_script(os.path.join(BACKEND_DIR, "agents/analyst_agent.js"))
        st.sidebar.success("Done!") if code == 0 else st.sidebar.error(err)
        st.rerun()

    if st.button("Publisher", use_container_width=True):
        with st.spinner("Running Publisher Agent..."):
            code, out, err = run_node_script(os.path.join(BACKEND_DIR, "agents/publisher_agent.js"))
        st.sidebar.success("Done!") if code == 0 else st.sidebar.error(err)
        st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.rerun()


# ── Main Area ─────────────────────────────────────────────────────────────────

st.title("🤖 PulseAI — Latest AI Updates")
st.markdown("A 4-agent pipeline that fetches, organizes, summarizes, and publishes the latest AI news.")
if topic:
    st.info(f"🔍 Research topic: **{topic}**")
st.divider()


# ── Section 1: Researcher Agent ───────────────────────────────────────────────

CATEGORY_ICONS = {
    "research":    "🔬",
    "lab_blogs":   "🏢",
    "newsletters": "📬",
    "news":        "📰",
    "community":   "💬",
}

st.header("📰 Researcher Agent")
st.markdown(
    "Claude searches **16 sources** across 5 categories: "
    "🔬 Research · 🏢 Lab Blogs · 📬 Newsletters · 📰 News · 💬 Community"
)

data = load_json("researcher_output.json")

if data is None:
    st.info("No data yet. Click **Researcher** or **Run Full Pipeline** in the sidebar.")
else:
    sources = data.get("sources_searched", [])
    st.caption(
        f"Last run: {data.get('timestamp', 'unknown')}  |  "
        f"Articles: {data.get('total', 0)}  |  "
        f"Sources searched: {len(sources)}"
    )

    articles = data.get("articles", [])
    categories = {}
    for article in articles:
        cat = article.get("category", "news")
        categories.setdefault(cat, []).append(article)

    for cat, cat_articles in categories.items():
        icon = CATEGORY_ICONS.get(cat, "📄")
        st.markdown(f"### {icon} {cat.replace('_', ' ').title()} ({len(cat_articles)})")
        for i, article in enumerate(cat_articles, 1):
            with st.expander(f"{i}. {article['title']}"):
                st.markdown(f"**Source:** {article.get('source', '—')}")
                st.markdown(f"**Summary:** {article.get('snippet', '—')}")
                if article.get("date"):
                    st.markdown(f"**Date:** {article['date']}")
                if article.get("link"):
                    st.markdown(f"[🔗 Read more]({article['link']})")

st.divider()


# ── Section 2: Analyst Agent ──────────────────────────────────────────────────

st.header("📋 Analyst Agent")
st.markdown("Claude organizes the raw articles into a structured 8-section report.")

data = load_json("analyst_output.json")

if data is None:
    st.info("No data yet. Run **Analyst** (requires Researcher output first).")
else:
    st.caption(f"Last run: {data.get('timestamp', 'unknown')}  |  Based on {data.get('source_articles', 0)} articles")
    st.markdown(data.get("report", "No report found."))

st.divider()


# ── Section 3: Synthesizer Agent ─────────────────────────────────────────────

st.header("🧠 Synthesizer Agent")
st.markdown("The report is sent to 5 AI models. Their responses are consolidated into one final summary.")

data = load_json("synthesizer_output.json")

if data is None:
    st.info("No data yet. Run **Synthesizer** (requires Analyst output first).")
else:
    st.caption(
        f"Last run: {data.get('timestamp', 'unknown')}  |  "
        f"{data.get('models_successful', 0)}/{data.get('models_queried', 5)} models succeeded"
    )

    st.markdown("### 🏆 Final Consolidated Summary")
    st.success(data.get("final_summary", "No summary."))

    st.markdown("### Individual Model Responses")

    MODEL_ICONS = {
        "Claude Opus 4.6":   "🟠",
        "GPT-4o":            "🟢",
        "Gemini 1.5 Pro":    "🔵",
        "Mistral Large":     "🟣",
        "Cohere Command R+": "🔴",
    }

    cols = st.columns(2)
    for i, response in enumerate(data.get("model_responses", [])):
        icon = MODEL_ICONS.get(response["model"], "🤖")
        with cols[i % 2]:
            with st.expander(f"{icon} {response['model']} — {status_badge(response['status'])}"):
                if response["status"] == "success":
                    st.markdown(response["summary"])
                else:
                    st.error(f"Error: {response.get('error', 'Unknown error')}")

st.divider()


# ── Section 4: Publisher Agent ────────────────────────────────────────────────

st.header("📤 Publisher Agent")
st.markdown("Sends the final summary via **Email** and posts to **LinkedIn**.")

data = load_json("publisher_output.json")

if data is None:
    st.info("No data yet. Run **Publisher** (requires Synthesizer output first).")
else:
    st.caption(f"Last run: {data.get('timestamp', 'unknown')}")

    col_email, col_linkedin = st.columns(2)

    with col_email:
        st.markdown("#### 📧 Email")
        email = data.get("email", {})
        st.markdown(f"**Status:** {status_badge(email.get('status', 'unknown'))}")
        if email.get("messageId"):
            st.markdown(f"**Message ID:** `{email['messageId']}`")
        if email.get("error"):
            st.error(email["error"])

    with col_linkedin:
        st.markdown("#### 💼 LinkedIn")
        linkedin = data.get("linkedin", {})
        st.markdown(f"**Status:** {status_badge(linkedin.get('status', 'unknown'))}")
        if linkedin.get("postId"):
            st.markdown(f"**Post ID:** `{linkedin['postId']}`")
        if linkedin.get("error"):
            st.error(linkedin["error"])

    st.markdown("#### 📝 LinkedIn Post Preview")
    st.text_area(
        "Post content",
        value=data.get("linkedin_post_preview", ""),
        height=250,
        disabled=True,
    )
