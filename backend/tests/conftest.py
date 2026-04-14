"""
Shared fixtures for PulseAI agent tests.
"""

import sys
from pathlib import Path

import pytest

# Make backend/ importable
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))


# ── Sample data fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def sample_articles():
    return [
        {
            "title": "Anthropic Releases Claude 3.5 Sonnet",
            "snippet": "Anthropic has released a new model with improved reasoning capabilities.",
            "link": "https://anthropic.com/blog/claude-3-5-sonnet",
            "source": "Anthropic Research",
            "category": "lab_blogs",
            "date": None,
        },
        {
            "title": "OpenAI GPT-5 Shows Breakthrough in Coding",
            "snippet": "OpenAI's latest model achieves state-of-the-art results on SWE-bench.",
            "link": "https://openai.com/blog/gpt-5",
            "source": "OpenAI Blog",
            "category": "lab_blogs",
            "date": None,
        },
        {
            "title": "Google DeepMind Gemini Ultra Benchmark Results",
            "snippet": "DeepMind's Gemini Ultra surpasses human experts on MMLU benchmark.",
            "link": "https://deepmind.google/gemini",
            "source": "Google DeepMind",
            "category": "research",
            "date": None,
        },
    ]


@pytest.fixture
def researcher_output(sample_articles):
    return {
        "timestamp": "2026-04-08T10:00:00",
        "topic": "Latest AI updates",
        "total": len(sample_articles),
        "sources_searched": ["Anthropic Research", "OpenAI Blog", "Google DeepMind"],
        "articles": sample_articles,
    }


@pytest.fixture
def analyst_output():
    return {
        "timestamp": "2026-04-08T10:05:00",
        "source_articles": 3,
        "report": (
            "## 1. Introduction\n"
            "Recent developments show rapid progress in LLMs.\n\n"
            "## 2. Existing Problems\n"
            "Hallucination and reasoning remain key challenges.\n\n"
            "## 3. Proposed Solutions\n"
            "Chain-of-thought and RLHF address many issues.\n\n"
            "## 4. Architecture Overview\n"
            "[LLM] --> [RLHF] --> [Output]\n\n"
            "## 5. Advantages\n"
            "Better accuracy and alignment.\n\n"
            "## 6. Disadvantages\n"
            "High compute cost.\n\n"
            "## 7. Applied AI Use Cases\n"
            "Code generation, summarization, reasoning.\n\n"
            "## 8. Future Implementation\n"
            "Multimodal agents and real-time reasoning expected."
        ),
    }


@pytest.fixture
def synthesizer_output():
    return {
        "timestamp": "2026-04-08T10:10:00",
        "models_queried": 5,
        "models_successful": 3,
        "model_responses": [
            {"model": "Llama 3.2", "status": "success", "summary": "LLMs are improving rapidly."},
            {"model": "Mistral", "status": "success", "summary": "Reasoning breakthroughs dominate."},
            {"model": "Qwen 2.5", "status": "success", "summary": "Multimodal models are trending."},
            {"model": "Phi-3", "status": "error", "error": "model not found", "summary": None},
            {"model": "Gemma 2", "status": "error", "error": "timeout", "summary": None},
        ],
        "final_summary": (
            "The AI landscape is rapidly evolving with breakthrough models from Anthropic, "
            "OpenAI, and Google DeepMind. Key trends include improved reasoning, multimodal "
            "capabilities, and alignment research."
        ),
    }


@pytest.fixture
def ddg_raw_results():
    """Raw DuckDuckGo results as returned by DDGS().text()."""
    return [
        {
            "title": "Claude 3.5 Sonnet Released",
            "body": "Anthropic releases new model with enhanced reasoning.",
            "href": "https://anthropic.com/claude-3-5",
        },
        {
            "title": "GPT-5 Coding Benchmarks",
            "body": "OpenAI GPT-5 achieves top scores on HumanEval.",
            "href": "https://openai.com/gpt-5",
        },
    ]
