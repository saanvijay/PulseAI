# ─────────────────────────────────────────────────────────────────────────────
# PulseAI — Source Configuration
#
# Uncomment any source to include it in the next research run.
# Each active source triggers one DuckDuckGo search call.
# Default: 3 sources for a quick test run.
# ─────────────────────────────────────────────────────────────────────────────

SOURCES = {

    "research": [
        # {"query": "site:arxiv.org/abs AI machine learning 2026",        "label": "ArXiv"},
        # {"query": "site:paperswithcode.com latest AI state of the art", "label": "Papers with Code"},
    ],

    "lab_blogs": [
        {"query": "Anthropic research latest AI 2026",               "label": "Anthropic Research"},
        {"query": "OpenAI blog latest news 2026",                    "label": "OpenAI Blog"},
        {"query": "Google DeepMind research 2026",                   "label": "Google DeepMind"},
        # {"query": "Meta AI blog latest 2026",                       "label": "Meta AI Blog"},
        # {"query": "Mistral AI news 2026",                           "label": "Mistral"},
        # {"query": "Hugging Face blog 2026",                         "label": "Hugging Face Blog"},
    ],

    "newsletters": [
        # {"query": "DeepLearning.AI The Batch newsletter 2026",      "label": "The Batch"},
        # {"query": "Import AI Jack Clark newsletter 2026",           "label": "Import AI"},
    ],

    "news": [
        # {"query": "site:venturebeat.com AI news 2026",              "label": "VentureBeat"},
        # {"query": "site:techcrunch.com artificial intelligence 2026", "label": "TechCrunch AI"},
        # {"query": "site:wired.com artificial intelligence 2026",    "label": "Wired AI"},
    ],

    "community": [
        # {"query": "reddit MachineLearning top posts 2026",          "label": "Reddit r/MachineLearning"},
        # {"query": "reddit LocalLLaMA top posts 2026",               "label": "Reddit r/LocalLLaMA"},
        # {"query": "LinkedIn AI artificial intelligence pulse 2026", "label": "LinkedIn"},
        # {"query": "AI breakthroughs twitter 2026",                  "label": "X/Twitter"},
    ],

}
