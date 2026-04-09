# ─────────────────────────────────────────────────────────────────────────────
# PulseAI — Token / Context Limits
#
# These control how much output each agent requests from Ollama.
# Adjust based on the model context window and your speed preferences.
# ─────────────────────────────────────────────────────────────────────────────

TOKENS = {
    "researcher": 4096,          # Ollama: organize raw DDG results into JSON
    "analyst": 4096,             # 8-section structured report
    "synthesizer_per_model": 1024,  # Each Ollama model's summary
    "synthesizer_final": 1024,   # Consolidation pass
    "trend": 256,                # Single short phrase
}
