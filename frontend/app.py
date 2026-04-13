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

for key, default in [
    ("topic",              ""),
    ("trend_topics",       []),
    ("research_mode",      False),
    ("research_gap_items", []),   # list of {topic, gap} dicts from research_gap_agent
]:
    if key not in st.session_state:
        st.session_state[key] = default


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


# Maps orchestrator step prefixes → display names
_STEP_LABELS = {
    "[Step 1/4]": "Researcher Agent",
    "[Step 2/4]": "Analyst Agent",
    "[Step 3/4]": "Synthesizer Agent",
    "[Step 4/4]": "Publisher Agent",
}

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
            # Update the displayed agent name as each pipeline step starts
            if agent_name in ("Full Pipeline", "Research Pipeline"):
                for prefix, label in _STEP_LABELS.items():
                    if line.startswith(prefix):
                        state["running"] = f"{agent_name} — {label}"
                        break
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
        "and displays a ready-to-publish article or structured research paper."
    )

    st.divider()

    # ── Status indicators ─────────────────────────────────────────────────────
    topic         = st.session_state.topic
    research_mode = st.session_state.research_mode

    si_col1, si_col2, si_col3 = st.columns(3)
    with si_col1:
        st.markdown("##### Current Agent")
        if busy:
            st.success(f"⚙️ Running: **{state['running']}**")
        else:
            last = state.get("last_agent")
            if last:
                st.info(f"✅ Last run: **{last}**")
            else:
                st.info("💤 Idle")
    with si_col2:
        st.markdown("##### Current Topic")
        if topic:
            st.success(f"🎯 {topic}")
        else:
            st.info("🌐 Latest AI updates (no topic set)")
    with si_col3:
        st.markdown("##### Output Mode")
        if research_mode:
            st.warning("🔬 Research Paper")
        else:
            st.info("📰 Article (LinkedIn / Blog)")

    st.divider()

    # ── Topic selection — three inner tabs ────────────────────────────────────
    st.markdown("##### Select Topic")
    ttab_manual, ttab_trend, ttab_gap = st.tabs([
        "✏️ Enter Manually",
        "🔍 Trending Topics",
        "🔬 Research Gap",
    ])

    with ttab_manual:
        st.caption("Type any topic and set it for the pipeline.")
        typed = st.text_input(
            "Topic",
            value=st.session_state.topic,
            placeholder="e.g. LLM reasoning, multimodal models, AI agents…",
            disabled=busy,
            label_visibility="collapsed",
        )
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            if st.button("✅ Set Topic", use_container_width=True, disabled=busy or not typed.strip()):
                st.session_state.topic = typed.strip()
                st.session_state.research_mode = False
                st.session_state.trend_topics = []
                st.session_state.research_gap_items = []
                st.rerun()
        with t_col2:
            if st.button("✖ Clear Topic", use_container_width=True, disabled=busy or not st.session_state.topic):
                st.session_state.topic = ""
                st.session_state.research_mode = False
                st.rerun()

    with ttab_trend:
        st.caption("Auto-detect the most trending AI topics from live news sources.")
        if st.button("🔍 Run Trend Agent", use_container_width=True, disabled=busy):
            st.session_state.trend_topics = []
            st.session_state.research_gap_items = []
            launch_agent("Trend Agent", os.path.join(BACKEND_DIR, "agents/trend_agent.py"))
            st.rerun()
        if st.session_state.trend_topics:
            st.markdown("**Select a trending topic:**")
            chosen = st.radio(
                "trending_radio",
                st.session_state.trend_topics,
                label_visibility="collapsed",
            )
            if st.button("Use this topic", use_container_width=True, key="use_trend"):
                st.session_state.topic = chosen
                st.session_state.research_mode = False
                st.session_state.trend_topics = []
                st.rerun()
        elif not busy:
            st.info("Click **Run Trend Agent** to fetch trending topics.")

    with ttab_gap:
        st.caption("Scan recent research papers and identify unexplored gaps. Output will be a structured research paper.")
        gap_broad = st.text_input(
            "Broad area (optional)",
            placeholder="e.g. computer vision, NLP, reinforcement learning…",
            disabled=busy,
            key="gap_broad_input",
            label_visibility="collapsed",
        )
        if st.button("🔬 Run Research Gap Agent", use_container_width=True, disabled=busy):
            st.session_state.trend_topics = []
            st.session_state.research_gap_items = []
            args = (gap_broad.strip(),) if gap_broad.strip() else ()
            launch_agent("Research Gap Agent", os.path.join(BACKEND_DIR, "agents/research_gap_agent.py"), args)
            st.rerun()
        if st.session_state.research_gap_items:
            st.markdown("**Select a research gap:**")
            gap_labels = [g["topic"] for g in st.session_state.research_gap_items]
            chosen_idx = st.radio(
                "gap_radio",
                range(len(gap_labels)),
                format_func=lambda i: gap_labels[i],
                label_visibility="collapsed",
            )
            chosen_gap = st.session_state.research_gap_items[chosen_idx]
            if chosen_gap.get("gap"):
                st.caption(f"📌 Gap: {chosen_gap['gap']}")
            if st.button("Use this research topic", use_container_width=True, key="use_gap"):
                st.session_state.topic = chosen_gap["topic"]
                st.session_state.research_mode = True
                st.session_state.research_gap_items = []
                st.session_state.trend_topics = []
                st.rerun()
        elif not busy:
            st.info("Click **Run Research Gap Agent** to discover research gaps.")

    st.divider()

    # ── Run buttons ───────────────────────────────────────────────────────────
    if research_mode:
        if st.button("🔬 Run Research Pipeline  (→ Research Paper)", use_container_width=True, type="primary", disabled=busy):
            args = (topic, "--research") if topic else ("--research",)
            launch_agent("Research Pipeline", os.path.join(BACKEND_DIR, "orchestrator.py"), args)
            st.rerun()
    else:
        if st.button("🚀 Run Full Pipeline  (→ Article)", use_container_width=True, type="primary", disabled=busy):
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
            agent_script = "agents/paper_writer_agent.py" if research_mode else "agents/publisher_agent.py"
            launch_agent("Publisher Agent", os.path.join(BACKEND_DIR, agent_script))
            st.rerun()

    st.divider()

    if st.button("🔄 Refresh Results", use_container_width=True, disabled=busy):
        st.rerun()

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
        scraped = sum(1 for a in data.get("articles", []) if a.get("full_content"))
        st.caption(
            f"Last run: {data.get('timestamp','?')}  |  "
            f"Articles: {data.get('total',0)}  |  "
            f"Full content scraped: {scraped}  |  "
            f"Sources: {len(data.get('sources_searched', []))}"
        )
        articles   = data.get("articles", [])
        categories = {}
        for a in articles:
            categories.setdefault(a.get("category", "news"), []).append(a)
        for cat, cat_articles in categories.items():
            icon = CATEGORY_ICONS.get(cat, "📄")
            st.markdown(f"### {icon} {cat.replace('_',' ').title()} ({len(cat_articles)})")
            for i, a in enumerate(cat_articles, 1):
                label = f"{i}. {a['title']}"
                if a.get("full_content"):
                    label += " ✦"
                with st.expander(label):
                    st.markdown(f"**Source:** {a.get('source','—')}")
                    if a.get("full_content"):
                        st.markdown(f"**Content (scraped):** {a['full_content'][:300]}…")
                    else:
                        st.markdown(f"**Snippet:** {a.get('snippet','—')}")
                    if a.get("date"):  st.markdown(f"**Date:** {a['date']}")
                    if a.get("link"):  st.markdown(f"[🔗 Read more]({a['link']})")
        st.caption("✦ = full article content scraped")


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
    data = load_json("publisher_output.json")

    is_research = data.get("mode") == "research" if data else False

    if is_research:
        st.markdown("### 🔬 Publisher Agent — Research Paper")
        st.markdown("> This paper was generated in **Research Mode**. Copy it to any research paper platform, Overleaf, or your institution's repository.")
        if data.get("gap"):
            st.info(f"📌 Research Gap Addressed: {data['gap']}")
    else:
        st.markdown("### 📤 Publisher Agent — Final Article")
        st.markdown("> Copy and paste this article to LinkedIn, Medium, Substack, or any blog platform.")

    if data is None:
        st.info("No data yet. Run the Publisher agent.")
    else:
        st.caption(f"Last run: {data.get('timestamp','?')}  |  Topic: {data.get('topic') or '—'}")
        article = data.get("final_article", "")

        if article:
            dl_col1, dl_col2 = st.columns(2)
            ext  = "md" if not is_research else "tex"
            mime = "text/markdown" if not is_research else "text/plain"
            name = "pulseai_paper" if is_research else "pulseai_article"
            with dl_col1:
                st.download_button(
                    "📥 Download as Markdown" if not is_research else "📥 Download as LaTeX (.tex)",
                    data=article,
                    file_name=f"{name}.{ext}",
                    mime=mime,
                    use_container_width=True,
                )
            with dl_col2:
                st.download_button(
                    "📄 Download as Text",
                    data=article,
                    file_name=f"{name}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        st.text_area(
            "Research Paper" if is_research else "Article",
            value=article,
            height=550,
            disabled=True,
        )


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
    last_agent = state.get("last_agent", "")
    if last_agent == "Trend Agent":
        trend = load_json("trend_output.json")
        if trend and trend.get("topics"):
            st.session_state.trend_topics      = trend["topics"]
            st.session_state.research_gap_items = []
    elif last_agent == "Research Gap Agent":
        gaps = load_json("research_gap_output.json")
        if gaps and gaps.get("gaps"):
            st.session_state.research_gap_items = gaps["gaps"]
            st.session_state.trend_topics       = []
    state["done"] = False
    time.sleep(0.3)
    st.rerun()
