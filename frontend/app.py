"""
PulseAI - Streamlit Dashboard for the Multi-Agent AI Pipeline
"""

import json
import os
import subprocess
import sys
import threading
import time
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PulseAI — Latest AI Updates",
    page_icon="🤖",
    layout="wide",
)

ROOT_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
OUTPUT_DIR  = os.path.join(BACKEND_DIR, "output")


# ── Session state ─────────────────────────────────────────────────────────────

if "topic" not in st.session_state:
    st.session_state.topic = ""
if "trend_topics" not in st.session_state:
    st.session_state.trend_topics = []


# ── Shared agent state (cache_resource = safe for background threads) ─────────

@st.cache_resource
def get_agent_state():
    return {"running": None, "logs": [], "process": None, "done": False}


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        return json.load(f)


def _agent_thread(agent_name, script_path, extra_args=()):
    state = get_agent_state()
    cmd   = [sys.executable, "-u", script_path, *extra_args]
    proc  = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, cwd=BACKEND_DIR,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    state["process"] = proc
    for raw in iter(proc.stdout.readline, ""):
        line = raw.rstrip()
        if line:
            state["logs"].append(line)
    proc.stdout.close()
    proc.wait()
    state["running"]    = None
    state["last_agent"] = agent_name
    state["done"]       = True
    state["process"]    = None


def launch_agent(agent_name, script_path, extra_args=()):
    state = get_agent_state()
    state.update({"running": agent_name, "last_agent": None, "logs": [], "done": False, "process": None})
    threading.Thread(target=_agent_thread, args=(agent_name, script_path, extra_args), daemon=True).start()


def status_badge(status):
    if status == "success": return "✅ Success"
    if status == "error":   return "❌ Error"
    if status == "skipped": return "⏭️ Skipped"
    return status


# ── State ─────────────────────────────────────────────────────────────────────

state = get_agent_state()
busy  = state["running"] is not None

st.title("🤖 PulseAI")

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_main, tab_researcher, tab_analyst, tab_synthesizer, tab_publisher, tab_log = st.tabs([
    "🏠 Pipeline",
    "🔎 Researcher",
    "📋 Analyst",
    "🧠 Synthesizer",
    "📤 Publisher",
    "📡 Log",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Pipeline controls
# ══════════════════════════════════════════════════════════════════════════════

with tab_main:
    st.markdown(
        "A **4-agent AI pipeline** powered by **CrewAI + Ollama** that fetches the latest AI news, "
        "organizes it into a structured report, summarizes it across multiple local models, "
        "and displays a ready-to-publish article."
    )

    st.divider()

    # Topic + Trend Agent
    st.markdown("##### Research Topic")
    topic = st.session_state.topic
    if topic:
        st.info(f"Current topic: **{topic}**")

    if st.button("🔍 Trend Agent — Auto-detect Topic", use_container_width=True, disabled=busy):
        st.session_state.trend_topics = []
        launch_agent("Trend Agent", os.path.join(BACKEND_DIR, "agents/trend_agent.py"))
        st.rerun()

    if st.session_state.trend_topics:
        st.markdown("**Select a trending topic:**")
        chosen = st.radio(
            "trending_radio",
            st.session_state.trend_topics,
            label_visibility="collapsed",
        )
        if st.button("Use this topic", use_container_width=True):
            st.session_state.topic = chosen
            st.session_state.trend_topics = []
            st.rerun()

    st.divider()

    # Full pipeline
    if st.button("🚀 Run Full Pipeline", use_container_width=True, type="primary", disabled=busy):
        args = (topic,) if topic else ()
        launch_agent("Full Pipeline", os.path.join(BACKEND_DIR, "orchestrator.py"), args)
        st.rerun()

    st.divider()

    # Individual agent buttons
    st.markdown("##### Run Individual Agents")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔎 Researcher",  use_container_width=True, disabled=busy):
            args = (topic,) if topic else ()
            launch_agent("Researcher Agent", os.path.join(BACKEND_DIR, "agents/researcher_agent.py"), args)
            st.rerun()
        if st.button("🧠 Synthesizer", use_container_width=True, disabled=busy):
            launch_agent("Synthesizer Agent", os.path.join(BACKEND_DIR, "agents/synthesizer_agent.py"))
            st.rerun()
    with c2:
        if st.button("📋 Analyst",   use_container_width=True, disabled=busy):
            launch_agent("Analyst Agent", os.path.join(BACKEND_DIR, "agents/analyst_agent.py"))
            st.rerun()
        if st.button("📤 Publisher", use_container_width=True, disabled=busy):
            launch_agent("Publisher Agent", os.path.join(BACKEND_DIR, "agents/publisher_agent.py"))
            st.rerun()

    st.divider()

    if st.button("🔄 Refresh Results", use_container_width=True, disabled=busy):
        st.rerun()

    # Running indicator
    if busy:
        st.info(f"⏳ Running: **{state['running']}** — check the **Log** tab for live output.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Researcher
# ══════════════════════════════════════════════════════════════════════════════

CATEGORY_ICONS = {"research": "🔬", "lab_blogs": "🏢", "newsletters": "📬", "news": "📰", "community": "💬"}

with tab_researcher:
    st.markdown("### 📰 Researcher Agent — Fetched Articles")
    data = load_json("researcher_output.json")
    if data is None:
        st.info("No data yet. Run the Researcher agent.")
    else:
        st.caption(f"Last run: {data.get('timestamp','?')}  |  Articles: {data.get('total',0)}  |  Sources: {len(data.get('sources_searched', []))}")
        articles   = data.get("articles", [])
        categories = {}
        for a in articles:
            categories.setdefault(a.get("category", "news"), []).append(a)
        for cat, cat_articles in categories.items():
            icon = CATEGORY_ICONS.get(cat, "📄")
            st.markdown(f"### {icon} {cat.replace('_',' ').title()} ({len(cat_articles)})")
            for i, a in enumerate(cat_articles, 1):
                with st.expander(f"{i}. {a['title']}"):
                    st.markdown(f"**Source:** {a.get('source','—')}")
                    st.markdown(f"**Summary:** {a.get('snippet','—')}")
                    if a.get("date"):  st.markdown(f"**Date:** {a['date']}")
                    if a.get("link"):  st.markdown(f"[🔗 Read more]({a['link']})")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Analyst
# ══════════════════════════════════════════════════════════════════════════════

with tab_analyst:
    st.markdown("### 📋 Analyst Agent — Structured Report")
    data = load_json("analyst_output.json")
    if data is None:
        st.info("No data yet. Run the Analyst agent.")
    else:
        st.caption(f"Last run: {data.get('timestamp','?')}  |  Based on {data.get('source_articles',0)} articles")
        st.markdown(data.get("report", "No report found."))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Synthesizer
# ══════════════════════════════════════════════════════════════════════════════

with tab_synthesizer:
    st.markdown("### 🧠 Synthesizer Agent — Multi-Model Summary")
    data = load_json("synthesizer_output.json")
    if data is None:
        st.info("No data yet. Run the Synthesizer agent.")
    else:
        st.caption(f"Last run: {data.get('timestamp','?')}  |  {data.get('models_successful',0)}/{data.get('models_queried',5)} models succeeded")
        st.markdown("### 🏆 Final Consolidated Summary")
        st.success(data.get("final_summary", "No summary."))
        st.markdown("### Individual Model Responses")
        MODEL_ICONS = {"Llama 3.2": "🟠", "Mistral": "🟢", "Qwen 2.5": "🔵", "Phi-3": "🟣", "Gemma 2": "🔴"}
        cols = st.columns(2)
        for i, r in enumerate(data.get("model_responses", [])):
            with cols[i % 2]:
                with st.expander(f"{MODEL_ICONS.get(r['model'],'🤖')} {r['model']} — {status_badge(r['status'])}"):
                    if r["status"] == "success": st.markdown(r["summary"])
                    else: st.error(r.get("error", "Unknown error"))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Publisher
# ══════════════════════════════════════════════════════════════════════════════

with tab_publisher:
    st.markdown("### 📤 Publisher Agent — Final Article")
    data = load_json("publisher_output.json")
    if data is None:
        st.info("No data yet. Run the Publisher agent.")
    else:
        st.caption(f"Last run: {data.get('timestamp','?')}")
        st.markdown("> Copy and paste this article to LinkedIn, Medium, Substack, or any blog platform.")
        article = data.get("final_article", "")
        st.text_area("Article", value=article, height=500, disabled=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — Log
# ══════════════════════════════════════════════════════════════════════════════

with tab_log:
    agent_name = state["running"]
    logs       = state["logs"]

    if agent_name:
        hdr, stop_btn = st.columns([4, 1])
        hdr.markdown(f"##### 📡 {agent_name} — Live Log")
        if stop_btn.button("⏹ Stop", use_container_width=True, type="secondary"):
            proc = state["process"]
            if proc:
                proc.terminate()
            state["running"] = None
            state["done"]    = False
            st.rerun()
    elif logs:
        last_agent = state.get("last_agent", "Agent")
        last       = logs[-1] if logs else ""
        st.markdown(f"##### 📡 {last_agent} — Log")
        if "error" in last.lower() or "failed" in last.lower():
            st.error("❌ Agent failed.")
        else:
            st.success("✅ Done!")
    else:
        st.markdown("##### 📋 Log")
        st.caption("Logs will appear here when an agent is running.")

    log_box = st.container(height=560, border=True)
    with log_box:
        if logs:
            st.code("\n".join(logs), language="bash")
        else:
            st.markdown(" ")

# ── Auto-refresh ──────────────────────────────────────────────────────────────

if agent_name:
    time.sleep(0.5)
    st.rerun()
elif state["done"]:
    if state.get("last_agent") == "Trend Agent":
        trend = load_json("trend_output.json")
        if trend and trend.get("topics"):
            st.session_state.trend_topics = trend["topics"]
    state["done"] = False
    time.sleep(0.3)
    st.rerun()
