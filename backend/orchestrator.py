# Orchestrator: Runs all 4 agents in sequence

import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from agents.researcher_agent import fetch_latest_ai_concepts
from agents.analyst_agent    import organize_content
from agents.synthesizer_agent import summarize_with_multiple_models
from agents.publisher_agent  import publish_results


def run_pipeline(topic: str = "") -> None:
    print("\n========================================")
    print("  PulseAI - Multi-Agent Pipeline")
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

    print("[Step 4/4] Publisher Agent: Publishing Results")
    t4 = time.time()
    publish_results()
    print(f"  Completed in {time.time() - t4:.1f}s\n")

    print("========================================")
    print(f"  Pipeline Complete! Total time: {time.time() - start:.1f}s")
    print("  Outputs saved to the output/ folder")
    print("========================================\n")


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        run_pipeline(topic)
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        sys.exit(1)
