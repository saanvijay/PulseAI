"""
PulseAI - Streamlit Dashboard for the Multi-Agent AI Pipeline
"""

import json
import os
import subprocess
import time
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


def run_node_script(script_path):
    """Run a Node.js script and stream its output to Streamlit."""
    result = subprocess.run(
        ["node", script_path],
        capture_output=True,
        text=True,
        cwd=BACKEND_DIR,
    )
    return result.returncode, result.stdout, result.stderr


def status_badge(status):
    if status == "success":
        return "✅ Success"
    elif status == "error":
        return "❌ Error"
    elif status == "skipped":
        return "⏭️ Skipped"
    return status


# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("🤖 PulseAI")
st.sidebar.markdown("Multi-agent pipeline for the latest AI updates.")
st.sidebar.divider()

st.sidebar.subheader("Run Agents")

if st.sidebar.button("🚀 Run Full Pipeline", use_container_width=True, type="primary"):
    with st.spinner("Running full pipeline (this takes a few minutes)..."):
        code, out, err = run_node_script(os.path.join(BACKEND_DIR, "orchestrator.js"))
    if code == 0:
        st.sidebar.success("Pipeline complete!")
    else:
        st.sidebar.error(f"Pipeline failed:\n{err}")
    st.rerun()

st.sidebar.divider()

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Researcher", use_container_width=True):
        with st.spinner("Running Researcher Agent..."):
            code, out, err = run_node_script(os.path.join(BACKEND_DIR, "agents/researcher_agent.js"))
        st.sidebar.success("Done!") if code == 0 else st.sidebar.error(err)
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

tab1, tab2, tab3, tab4 = st.tabs([
    "📰 Researcher Agent",
    "📋 Analyst Agent",
    "🧠 Synthesizer Agent",
    "📤 Publisher Agent",
])


# ── Tab 1: Agent 1 output ─────────────────────────────────────────────────────

CATEGORY_ICONS = {
    "research":    "🔬",
    "lab_blogs":   "🏢",
    "newsletters": "📬",
    "news":        "📰",
    "community":   "💬",
}

with tab1:
    st.subheader("Agent 1 — Fetched AI Articles")
    st.markdown(
        "Claude searches **16 sources** across 5 categories: "
        "🔬 Research · 🏢 Lab Blogs · 📬 Newsletters · 📰 News · 💬 Community"
    )

    data = load_json("agent1_output.json")

    if data is None:
        st.info("No data yet. Click **Agent 1** or **Run Full Pipeline** in the sidebar.")
    else:
        sources = data.get("sources_searched", [])
        st.caption(
            f"Last run: {data.get('timestamp', 'unknown')}  |  "
            f"Articles: {data.get('total', 0)}  |  "
            f"Sources searched: {len(sources)}"
        )

        articles = data.get("articles", [])

        # Group articles by category for display
        categories = {}
        for article in articles:
            cat = article.get("category", "news")
            categories.setdefault(cat, []).append(article)

        for cat, cat_articles in categories.items():
            icon = CATEGORY_ICONS.get(cat, "📄")
            st.markdown(f"### {icon} {cat.replace('_', ' ').title()} ({len(cat_articles)})")
            for i, article in enumerate(cat_articles, 1):
                label = f"{i}. {article['title']}"
                with st.expander(label):
                    st.markdown(f"**Source:** {article.get('source', '—')}")
                    st.markdown(f"**Summary:** {article.get('snippet', '—')}")
                    if article.get("date"):
                        st.markdown(f"**Date:** {article['date']}")
                    if article.get("link"):
                        st.markdown(f"[🔗 Read more]({article['link']})")


# ── Tab 2: Agent 2 output ─────────────────────────────────────────────────────

with tab2:
    st.subheader("Agent 2 — Organized Technical Report")
    st.markdown("Claude organizes the raw articles into a structured 8-section report.")

    data = load_json("agent2_output.json")

    if data is None:
        st.info("No data yet. Run Agent 2 (requires Agent 1 output first).")
    else:
        st.caption(f"Last run: {data.get('timestamp', 'unknown')}  |  Based on {data.get('source_articles', 0)} articles")
        st.markdown(data.get("report", "No report found."))


# ── Tab 3: Agent 3 output ─────────────────────────────────────────────────────

with tab3:
    st.subheader("Agent 3 — Multi-Model Summary")
    st.markdown("The report is sent to 5 AI models. Their responses are consolidated into one final summary.")

    data = load_json("agent3_output.json")

    if data is None:
        st.info("No data yet. Run Agent 3 (requires Agent 2 output first).")
    else:
        st.caption(
            f"Last run: {data.get('timestamp', 'unknown')}  |  "
            f"{data.get('models_successful', 0)}/{data.get('models_queried', 5)} models succeeded"
        )

        # Final summary at the top
        st.markdown("### 🏆 Final Consolidated Summary")
        st.success(data.get("final_summary", "No summary."))

        st.divider()

        # Individual model responses
        st.markdown("### Individual Model Responses")

        MODEL_ICONS = {
            "Claude Opus 4.6": "🟠",
            "GPT-4o": "🟢",
            "Gemini 1.5 Pro": "🔵",
            "Mistral Large": "🟣",
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


# ── Tab 4: Agent 4 output ─────────────────────────────────────────────────────

with tab4:
    st.subheader("Agent 4 — Publish Results")
    st.markdown("Sends the final summary via **Email** and posts to **LinkedIn**.")

    data = load_json("agent4_output.json")

    if data is None:
        st.info("No data yet. Run Agent 4 (requires Agent 3 output first).")
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

        st.divider()
        st.markdown("#### 📝 LinkedIn Post Preview")
        st.text_area(
            "Post content",
            value=data.get("linkedin_post_preview", ""),
            height=250,
            disabled=True,
        )
