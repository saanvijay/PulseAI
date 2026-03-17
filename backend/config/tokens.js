// ─────────────────────────────────────────────────────────────────────────────
// PulseAI — Token Limit Configuration
//
// Controls max_tokens for every Claude / OpenRouter API call.
// Lower values = faster & cheaper. Higher values = more detailed output.
// ─────────────────────────────────────────────────────────────────────────────

export const TOKENS = {

  // Agent 1 — Researcher
  // Claude searches all active sources and returns a JSON array of articles.
  // Needs enough room for 25-30 article objects.
  researcher: 8000,

  // Agent 2 — Analyst
  // Claude writes an 8-section structured report from the raw articles.
  analyst: 4000,

  // Agent 3 — Synthesizer
  // Each model writes a short summary (3-4 key insights).
  synthesizer_per_model: 1000,

  // Agent 3 — Final consolidated summary written by Claude.
  synthesizer_final: 1000,

  // Agent 4 — Trend
  // Claude returns a single short phrase (3-6 words). Keep this low.
  trend: 50,

};
