# Agent 4: Display the final article.
# No LLM needed here — pure display agent.

import json
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

INPUT_FILE = BASE_DIR / "output" / "synthesizer_output.json"
OUTPUT_FILE = BASE_DIR / "output" / "publisher_output.json"

# ── Main agent function ────────────────────────────────────────────────────────


def publish_results() -> dict:
    print("Agent 4: Displaying final article...")

    input_data = json.loads(INPUT_FILE.read_text())
    final_summary = input_data["final_summary"]

    print("\n" + "=" * 60)
    print("FINAL ARTICLE")
    print("=" * 60)
    print(final_summary)
    print("=" * 60 + "\n")

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "final_article": final_summary,
        "status": "displayed",
    }

    OUTPUT_FILE.write_text(json.dumps(results, indent=2))
    print("Agent 4: Done!")
    return results


if __name__ == "__main__":
    publish_results()
