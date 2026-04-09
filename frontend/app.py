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
    cmd   = [sys.executable, script_path, *extra_args]
    proc  = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, cwd=BACKEND_DIR,
    )
    state["process"] = proc
    for raw in iter(proc.stdout.readline, ""):
        line = raw.rstrip()
        if line:
            state["logs"].append(line)
    proc.stdout.close()
    proc.wait()
    state["running"] = None
    state["done"]    = True
    state["process"] = None


def launch_agent(agent_name, script_path, extra_args=()):
    state = get_agent_state()
    state.update({"running": agent_name, "logs": [], "done": False, "process": None})
    threading.Thread(target=_agent_thread, args=(agent_name, script_path, extra_args), daemon=True).start()


def status_badge(status):
    if status == "success": return "✅ Success"
    if status == "error":   return "❌ Error"
    if status == "skipped": return "⏭️ Skipped"
    return status


# ── Layout: left controls | right live log ────────────────────────────────────

state = get_agent_state()
busy  = state["running"] is not None

st.markdown("""
<style>
div[data-testid="stColumn"]:has(span.btn-apply) [data-testid="stButton"] button {
    background-color: #28a745 !important;
    border-color: #28a745 !important;
    color: white !important;
}
div[data-testid="stColumn"]:has(span.btn-apply) [data-testid="stButton"] button:hover {
    background-color: #218838 !important;
    border-color: #1e7e34 !important;
}
div[data-testid="stColumn"]:has(span.btn-agent) [data-testid="stButton"] button {
    background-color: #555555 !important;
    border-color: #555555 !important;
    color: white !important;
}
div[data-testid="stColumn"]:has(span.btn-agent) [data-testid="stButton"] button:hover {
    background-color: #444444 !important;
    border-color: #444444 !important;
}
</style>
""", unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")

# ══════════════════════════════════════════════════════════════════════════════
# LEFT — Controls
# ══════════════════════════════════════════════════════════════════════════════

with left:
    st.title("🤖 PulseAI")
    st.markdown(
        "A **4-agent AI pipeline** powered by **CrewAI + Ollama** that fetches the latest AI news, "
        "organizes it into a structured report, summarizes it across multiple local models, "
        "and publishes the result via Email and LinkedIn."
    )

    st.divider()

    # Topic input + Trend Agent
    st.markdown("##### Research Topic")
    inp_col, btn_col = st.columns([5, 1], vertical_alignment="bottom")
    with inp_col:
        topic_input = st.text_input(
            "topic",
            value=st.session_state.topic,
            placeholder="e.g. LLM reasoning, AI agents... (leave blank for general AI news)",
            label_visibility="collapsed",
            disabled=busy,
        )
    with btn_col:
        st.markdown('<span class="btn-apply"></span>', unsafe_allow_html=True)
        if st.button("Apply", use_container_width=True, disabled=busy):
            st.session_state.topic = topic_input
            st.rerun()
    topic = st.session_state.topic

    if st.button("🔍 Trend Agent — Auto-detect Topic", use_container_width=True, disabled=busy):
        if topic.strip():
            st.info("Topic already set. Clear the box to auto-detect.")
        else:
            launch_agent("Trend Agent", os.path.join(BACKEND_DIR, "agents/trend_agent.py"))
            st.rerun()

    st.divider()

    # Individual agent buttons
    st.markdown("##### Run Individual Agents")
    a_col, b_col = st.columns(2)
    with a_col:
        st.markdown('<span class="btn-agent"></span>', unsafe_allow_html=True)
        if st.button("🔎 Researcher",  use_container_width=True, disabled=busy):
            args = (topic,) if topic else ()
            launch_agent("Researcher Agent", os.path.join(BACKEND_DIR, "agents/researcher_agent.py"), args)
            st.rerun()
        if st.button("🧠 Synthesizer", use_container_width=True, disabled=busy):
            launch_agent("Synthesizer Agent", os.path.join(BACKEND_DIR, "agents/synthesizer_agent.py"))
            st.rerun()
    with b_col:
        st.markdown('<span class="btn-agent"></span>', unsafe_allow_html=True)
        if st.button("📋 Analyst",   use_container_width=True, disabled=busy):
            launch_agent("Analyst Agent", os.path.join(BACKEND_DIR, "agents/analyst_agent.py"))
            st.rerun()
        if st.button("📤 Publisher", use_container_width=True, disabled=busy):
            launch_agent("Publisher Agent", os.path.join(BACKEND_DIR, "agents/publisher_agent.py"))
            st.rerun()

    st.divider()

    # Full pipeline
    if st.button("🚀 Run Full Pipeline", use_container_width=True, type="primary", disabled=busy):
        args = (topic,) if topic else ()
        launch_agent("Full Pipeline", os.path.join(BACKEND_DIR, "orchestrator.py"), args)
        st.rerun()

    if st.button("🔄 Refresh Results", use_container_width=True, disabled=busy):
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RIGHT — Live log window
# ══════════════════════════════════════════════════════════════════════════════

with right:
    agent_name = state["running"]
    logs       = state["logs"]
    done       = state["done"]

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
        last = logs[-1] if logs else ""
        if "error" in last.lower() or "failed" in last.lower():
            st.error("❌ Agent failed.")
        else:
            st.success("✅ Done!")
    else:
        st.markdown("##### 📋 Live Log")
        st.caption("Logs will appear here when an agent is running.")

    # Log display in a fixed-height scrollable box
    log_box = st.container(height=520, border=True)
    with log_box:
        if logs:
            st.code("\n".join(logs), language="bash")
        else:
            st.markdown(" ")   # keep the box visible when empty

    # Auto-refresh while running; one final rerun when done
    if agent_name:
        time.sleep(0.5)
        st.rerun()
    elif done:
        if not st.session_state.topic.strip():
            trend = load_json("trend_output.json")
            if trend and trend.get("topic"):
                st.session_state.topic = trend["topic"]
        state["done"] = False
        time.sleep(0.3)
        st.rerun()


# ── Agent output sections ─────────────────────────────────────────────────────

st.divider()

# ── Researcher ────────────────────────────────────────────────────────────────

CATEGORY_ICONS = {"research": "🔬", "lab_blogs": "🏢", "newsletters": "📬", "news": "📰", "community": "💬"}

with st.expander("📰 Researcher Agent — Fetched Articles", expanded=True):
    data = load_json("researcher_output.json")
    if data is None:
        st.info("No data yet. Run the Researcher agent.")
    else:
        sources = data.get("sources_searched", [])
        st.caption(f"Last run: {data.get('timestamp','?')}  |  Articles: {data.get('total',0)}  |  Sources: {len(sources)}")
        articles = data.get("articles", [])
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

# ── Analyst ───────────────────────────────────────────────────────────────────

with st.expander("📋 Analyst Agent — Structured Report", expanded=False):
    data = load_json("analyst_output.json")
    if data is None:
        st.info("No data yet. Run the Analyst agent.")
    else:
        st.caption(f"Last run: {data.get('timestamp','?')}  |  Based on {data.get('source_articles',0)} articles")
        st.markdown(data.get("report", "No report found."))

# ── Synthesizer ───────────────────────────────────────────────────────────────

with st.expander("🧠 Synthesizer Agent — Multi-Model Summary", expanded=False):
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

# ── Publisher ─────────────────────────────────────────────────────────────────

with st.expander("📤 Publisher Agent — Email & LinkedIn", expanded=False):
    data = load_json("publisher_output.json")
    if data is None:
        st.info("No data yet. Run the Publisher agent.")
    else:
        st.caption(f"Last run: {data.get('timestamp','?')}")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📧 Email")
            email = data.get("email", {})
            st.markdown(f"**Status:** {status_badge(email.get('status','unknown'))}")
            if email.get("messageId"): st.markdown(f"**Message ID:** `{email['messageId']}`")
            if email.get("error"):     st.error(email["error"])
        with c2:
            st.markdown("#### 💼 LinkedIn")
            li = data.get("linkedin", {})
            st.markdown(f"**Status:** {status_badge(li.get('status','unknown'))}")
            if li.get("postId"):  st.markdown(f"**Post ID:** `{li['postId']}`")
            if li.get("error"):   st.error(li["error"])
        st.markdown("#### 📝 LinkedIn Post Preview")
        st.text_area("Post content", value=data.get("linkedin_post_preview",""), height=200, disabled=True)
