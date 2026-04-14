"""
Integration test for the PulseAI multi-agent pipeline.

Tests the full pipeline end-to-end with all external services mocked:
  - Google News RSS (search_batch_parallel / scrape_articles_parallel)
  - Ollama / CrewAI (LLM factory, Agent, Task, Crew)
  - Ollama direct API (synthesizer per-model calls)
  - File I/O (uses tmp_path to avoid touching the real output/ directory)

The integration test verifies:
  1. Agents run in the correct sequence (researcher → analyst → synthesizer → publisher)
  2. Data flows correctly between agents via JSON files
  3. Each agent produces the expected output schema
  4. The orchestrator wires everything together correctly
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# ── Sample fixtures ────────────────────────────────────────────────────────────

SAMPLE_ARTICLES = [
    {
        "title": "Claude 3.5 Sonnet Released",
        "snippet": "Anthropic releases new model with improved reasoning.",
        "link": "https://anthropic.com/claude",
        "source": "Anthropic Research",
        "category": "lab_blogs",
        "date": None,
    },
    {
        "title": "GPT-5 Achieves New Benchmarks",
        "snippet": "OpenAI's GPT-5 tops SWE-bench and MMLU leaderboards.",
        "link": "https://openai.com/gpt-5",
        "source": "OpenAI Blog",
        "category": "lab_blogs",
        "date": None,
    },
]

SAMPLE_REPORT = (
    "## 1. Introduction\nAI is evolving rapidly.\n"
    "## 2. Existing Problems\nHallucination persists.\n"
    "## 3. Proposed Solutions\nRLHF and RLVR.\n"
    "## 4. Architecture Overview\n[LLM]-->[RLHF]-->[Output]\n"
    "## 5. Advantages\nBetter alignment.\n"
    "## 6. Disadvantages\nHigh cost.\n"
    "## 7. Applied AI Use Cases\nCode, reasoning, search.\n"
    "## 8. Future Implementation\nMultimodal agents."
)

FINAL_SUMMARY = (
    "AI is advancing rapidly with major releases from Anthropic, OpenAI, and Google. "
    "Key highlights include improved reasoning, multimodal capabilities, and better alignment."
)


def _make_crew_result(text: str):
    mock_result = MagicMock()
    mock_result.__str__ = lambda self: text
    return mock_result


def _make_ollama_response(text: str):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": text}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _patch_agent_files(tmp_path, monkeypatch):
    """Redirect all agent INPUT_FILE / OUTPUT_FILE paths to tmp_path."""
    researcher_out = tmp_path / "researcher_output.json"
    analyst_out = tmp_path / "analyst_output.json"
    synthesizer_out = tmp_path / "synthesizer_output.json"
    publisher_out = tmp_path / "publisher_output.json"

    import agents.analyst_agent as aa
    import agents.publisher_agent as pa
    import agents.researcher_agent as ra
    import agents.synthesizer_agent as sa

    monkeypatch.setattr(ra, "OUTPUT_FILE", researcher_out)
    monkeypatch.setattr(aa, "INPUT_FILE", researcher_out)
    monkeypatch.setattr(aa, "OUTPUT_FILE", analyst_out)
    monkeypatch.setattr(sa, "INPUT_FILE", analyst_out)
    monkeypatch.setattr(sa, "OUTPUT_FILE", synthesizer_out)
    monkeypatch.setattr(pa, "INPUT_FILE", synthesizer_out)
    monkeypatch.setattr(pa, "OUTPUT_FILE", publisher_out)

    return researcher_out, analyst_out, synthesizer_out, publisher_out


# ── Integration: Full pipeline ────────────────────────────────────────────────


class TestFullPipeline:
    @patch("agents.synthesizer_agent.requests.post")
    @patch("agents.synthesizer_agent.get_llm")
    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.analyst_agent.get_llm")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.researcher_agent.scrape_articles_parallel")
    @patch("agents.researcher_agent.search_batch_parallel")
    def test_pipeline_runs_all_four_agents(
        self,
        mock_r_search,
        mock_r_scrape,
        mock_a_agent,
        mock_a_task,
        mock_a_crew,
        mock_a_get_llm,
        mock_s_agent,
        mock_s_task,
        mock_s_crew,
        mock_s_get_llm,
        mock_s_post,
        tmp_path,
        monkeypatch,
    ):
        r_out, a_out, s_out, p_out = _patch_agent_files(tmp_path, monkeypatch)

        mock_r_search.return_value = SAMPLE_ARTICLES
        mock_a_crew.return_value.kickoff.return_value = _make_crew_result(SAMPLE_REPORT)
        mock_s_post.return_value = _make_ollama_response("Key insight.")
        mock_s_crew.return_value.kickoff.return_value = _make_crew_result(FINAL_SUMMARY)

        from orchestrator import run_pipeline

        run_pipeline()

        assert r_out.exists(), "researcher_output.json was not created"
        assert a_out.exists(), "analyst_output.json was not created"
        assert s_out.exists(), "synthesizer_output.json was not created"
        assert p_out.exists(), "publisher_output.json was not created"

    @patch("agents.synthesizer_agent.requests.post")
    @patch("agents.synthesizer_agent.get_llm")
    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.analyst_agent.get_llm")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.researcher_agent.scrape_articles_parallel")
    @patch("agents.researcher_agent.search_batch_parallel")
    def test_data_flows_correctly_between_agents(
        self,
        mock_r_search,
        mock_r_scrape,
        mock_a_agent,
        mock_a_task,
        mock_a_crew,
        mock_a_get_llm,
        mock_s_agent,
        mock_s_task,
        mock_s_crew,
        mock_s_get_llm,
        mock_s_post,
        tmp_path,
        monkeypatch,
    ):
        r_out, a_out, s_out, p_out = _patch_agent_files(tmp_path, monkeypatch)

        mock_r_search.return_value = SAMPLE_ARTICLES
        mock_a_crew.return_value.kickoff.return_value = _make_crew_result(SAMPLE_REPORT)
        mock_s_post.return_value = _make_ollama_response("Key insight.")
        mock_s_crew.return_value.kickoff.return_value = _make_crew_result(FINAL_SUMMARY)

        from orchestrator import run_pipeline

        run_pipeline()

        r_data = json.loads(r_out.read_text())
        assert "articles" in r_data
        assert "sources_searched" in r_data

        a_data = json.loads(a_out.read_text())
        assert a_data["source_articles"] == len(r_data["articles"])

        s_data = json.loads(s_out.read_text())
        assert "final_summary" in s_data
        assert s_data["final_summary"] == FINAL_SUMMARY

        p_data = json.loads(p_out.read_text())
        assert "final_article" in p_data
        assert p_data["final_article"] == FINAL_SUMMARY

    @patch("agents.synthesizer_agent.requests.post")
    @patch("agents.synthesizer_agent.get_llm")
    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.analyst_agent.get_llm")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.researcher_agent.scrape_articles_parallel")
    @patch("agents.researcher_agent.search_batch_parallel")
    def test_pipeline_output_schemas_are_valid(
        self,
        mock_r_search,
        mock_r_scrape,
        mock_a_agent,
        mock_a_task,
        mock_a_crew,
        mock_a_get_llm,
        mock_s_agent,
        mock_s_task,
        mock_s_crew,
        mock_s_get_llm,
        mock_s_post,
        tmp_path,
        monkeypatch,
    ):
        r_out, a_out, s_out, p_out = _patch_agent_files(tmp_path, monkeypatch)

        mock_r_search.return_value = SAMPLE_ARTICLES
        mock_a_crew.return_value.kickoff.return_value = _make_crew_result(SAMPLE_REPORT)
        mock_s_post.return_value = _make_ollama_response("Insight.")
        mock_s_crew.return_value.kickoff.return_value = _make_crew_result(FINAL_SUMMARY)

        from orchestrator import run_pipeline

        run_pipeline()

        r = json.loads(r_out.read_text())
        assert all(k in r for k in ("timestamp", "topic", "total", "sources_searched", "articles"))

        a = json.loads(a_out.read_text())
        assert all(k in a for k in ("timestamp", "source_articles", "report"))
        assert isinstance(a["report"], str)

        s = json.loads(s_out.read_text())
        assert all(
            k in s for k in ("timestamp", "models_queried", "models_successful", "model_responses", "final_summary")
        )
        assert isinstance(s["model_responses"], list)

        p = json.loads(p_out.read_text())
        assert all(k in p for k in ("timestamp", "final_article", "status"))
        assert p["status"] == "displayed"

    @patch("agents.synthesizer_agent.requests.post")
    @patch("agents.synthesizer_agent.get_llm")
    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.analyst_agent.get_llm")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.researcher_agent.scrape_articles_parallel")
    @patch("agents.researcher_agent.search_batch_parallel")
    def test_pipeline_with_topic_argument(
        self,
        mock_r_search,
        mock_r_scrape,
        mock_a_agent,
        mock_a_task,
        mock_a_crew,
        mock_a_get_llm,
        mock_s_agent,
        mock_s_task,
        mock_s_crew,
        mock_s_get_llm,
        mock_s_post,
        tmp_path,
        monkeypatch,
    ):
        r_out, a_out, s_out, p_out = _patch_agent_files(tmp_path, monkeypatch)

        mock_r_search.return_value = SAMPLE_ARTICLES
        mock_a_crew.return_value.kickoff.return_value = _make_crew_result(SAMPLE_REPORT)
        mock_s_post.return_value = _make_ollama_response("Insight.")
        mock_s_crew.return_value.kickoff.return_value = _make_crew_result(FINAL_SUMMARY)

        from orchestrator import run_pipeline

        run_pipeline(topic="agentic AI systems")

        r = json.loads(r_out.read_text())
        assert r["topic"] == "agentic AI systems"

    @patch("agents.synthesizer_agent.requests.post")
    @patch("agents.synthesizer_agent.get_llm")
    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.analyst_agent.get_llm")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.researcher_agent.scrape_articles_parallel")
    @patch("agents.researcher_agent.search_batch_parallel")
    def test_pipeline_result_is_displayed(
        self,
        mock_r_search,
        mock_r_scrape,
        mock_a_agent,
        mock_a_task,
        mock_a_crew,
        mock_a_get_llm,
        mock_s_agent,
        mock_s_task,
        mock_s_crew,
        mock_s_get_llm,
        mock_s_post,
        tmp_path,
        monkeypatch,
    ):
        r_out, a_out, s_out, p_out = _patch_agent_files(tmp_path, monkeypatch)

        mock_r_search.return_value = SAMPLE_ARTICLES
        mock_a_crew.return_value.kickoff.return_value = _make_crew_result(SAMPLE_REPORT)
        mock_s_post.return_value = _make_ollama_response("Insight.")
        mock_s_crew.return_value.kickoff.return_value = _make_crew_result(FINAL_SUMMARY)

        from orchestrator import run_pipeline

        run_pipeline()

        p = json.loads(p_out.read_text())
        assert p["status"] == "displayed"
        assert p["final_article"] == FINAL_SUMMARY

    # ── Dependency chain tests ────────────────────────────────────────────────

    def test_analyst_fails_if_researcher_output_missing(self, tmp_path, monkeypatch):
        """Analyst agent must raise if researcher_output.json doesn't exist."""
        import agents.analyst_agent as aa

        monkeypatch.setattr(aa, "INPUT_FILE", tmp_path / "researcher_output.json")

        from agents.analyst_agent import organize_content

        with pytest.raises((FileNotFoundError, OSError)):
            organize_content()

    def test_synthesizer_fails_if_analyst_output_missing(self, tmp_path, monkeypatch):
        """Synthesizer must raise if analyst_output.json doesn't exist."""
        import agents.synthesizer_agent as sa

        monkeypatch.setattr(sa, "INPUT_FILE", tmp_path / "analyst_output.json")

        from agents.synthesizer_agent import summarize_with_multiple_models

        with pytest.raises((FileNotFoundError, OSError)):
            summarize_with_multiple_models()

    def test_publisher_fails_if_synthesizer_output_missing(self, tmp_path, monkeypatch):
        """Publisher must raise if synthesizer_output.json doesn't exist."""
        import agents.publisher_agent as pa

        monkeypatch.setattr(pa, "INPUT_FILE", tmp_path / "synthesizer_output.json")

        from agents.publisher_agent import publish_results

        with pytest.raises((FileNotFoundError, OSError)):
            publish_results()
