# Orchestrator: Runs all 4 agents in sequence.
# Usage:
#   python orchestrator.py                     # default pipeline
#   python orchestrator.py "topic"             # with topic
#   python orchestrator.py "topic" --research  # research paper mode

import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from agents.researcher_agent  import fetch_latest_ai_concepts
from agents.analyst_agent     import organize_content
from agents.synthesizer_agent import summarize_with_multiple_models
from agents.publisher_agent   import publish_results
from agents.paper_writer_agent import write_research_paper


def run_pipeline(topic: str = "", research_mode: bool = False) -> None:
    mode_label = "Research Paper" if research_mode else "Article"
    print("\n========================================")
    print(f"  PulseAI - Multi-Agent Pipeline ({mode_label} mode)")
    if topic:
        print(f"  Topic: {topic}")
    print("========================================\n")

    start = time.time()

    print("\n[Step 1/4] Researcher Agent: Fetching AI News")
    t1 = time.time()
    fetch_latest_ai_concepts(topic)
    print(f"  Completed in {time.time() - t1:.1f}s\n")

    print("[Step 2/4] Analyst Agent: Organizing Content")
    t2 = time.time()
    organize_content()
    print(f"  Completed in {time.time() - t2:.1f}s\n")

    print("[Step 3/4] Synthesizer Agent: Multi-Model Summary")
    t3 = time.time()
    summarize_with_multiple_models()
    print(f"  Completed in {time.time() - t3:.1f}s\n")

    if research_mode:
        print("[Step 4/4] Paper Writer Agent: Writing Research Paper")
        t4 = time.time()
        write_research_paper()
    else:
        print("[Step 4/4] Publisher Agent: Displaying Article")
        t4 = time.time()
        publish_results()
    print(f"  Completed in {time.time() - t4:.1f}s\n")

    print("========================================")
    print(f"  Pipeline Complete! Total time: {time.time() - start:.1f}s")
    print("  Outputs saved to the output/ folder")
    print("========================================\n")


if __name__ == "__main__":
    args          = sys.argv[1:]
    research_mode = "--research" in args
    topic_args    = [a for a in args if not a.startswith("--")]
    topic         = topic_args[0] if topic_args else ""
    try:
        run_pipeline(topic, research_mode)
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        sys.exit(1)
