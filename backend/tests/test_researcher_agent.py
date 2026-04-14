"""
Unit tests for Agent 1: Researcher Agent.

Mocks:
  - DDGS().text()        — DuckDuckGo search
  - crewai.Crew.kickoff  — Ollama / CrewAI pipeline
  - Path.write_text      — file output
"""

import json
from unittest.mock import MagicMock, patch

# ── ddg_search ────────────────────────────────────────────────────────────────


class TestDdgSearch:
    def test_returns_list_on_success(self, ddg_raw_results):
        with patch("agents.researcher_agent.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = ddg_raw_results
            from agents.researcher_agent import ddg_search

            result = ddg_search("AI news", max_results=2)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["title"] == "Claude 3.5 Sonnet Released"

    def test_returns_empty_list_on_exception(self):
        with patch("agents.researcher_agent.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.side_effect = Exception("network error")
            from agents.researcher_agent import ddg_search

            result = ddg_search("AI news")

        assert result == []

    def test_passes_max_results_to_ddgs(self, ddg_raw_results):
        with patch("agents.researcher_agent.DDGS") as mock_ddgs:
            mock_ctx = mock_ddgs.return_value.__enter__.return_value
            mock_ctx.text.return_value = ddg_raw_results
            from agents.researcher_agent import ddg_search

            ddg_search("test query", max_results=7)

        mock_ctx.text.assert_called_once_with("test query", max_results=7)


# ── fetch_latest_ai_concepts ──────────────────────────────────────────────────


class TestFetchLatestAiConcepts:
    """All external I/O is mocked: DDG, CrewAI, and file writes."""

    def _make_crew_result(self, articles):
        """Return a mock Crew kickoff result whose str() is a JSON array."""
        mock_result = MagicMock()
        mock_result.__str__ = lambda self: json.dumps(articles)
        return mock_result

    # Patch Agent and Task in addition to Crew/LLM to bypass Pydantic validation
    @patch("agents.researcher_agent.OUTPUT_FILE")
    @patch("agents.researcher_agent.Crew")
    @patch("agents.researcher_agent.Task")
    @patch("agents.researcher_agent.Agent")
    @patch("agents.researcher_agent.LLM")
    @patch("agents.researcher_agent.ddg_search")
    def test_returns_correct_schema(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output_file, sample_articles
    ):
        mock_ddg.return_value = [{"title": "t", "body": "s", "href": "http://x.com"}]
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(sample_articles)
        mock_output_file.parent.mkdir = MagicMock()
        mock_output_file.write_text = MagicMock()

        from agents.researcher_agent import fetch_latest_ai_concepts

        output = fetch_latest_ai_concepts()

        assert "timestamp" in output
        assert "topic" in output
        assert "total" in output
        assert "sources_searched" in output
        assert "articles" in output
        assert isinstance(output["articles"], list)

    @patch("agents.researcher_agent.OUTPUT_FILE")
    @patch("agents.researcher_agent.Crew")
    @patch("agents.researcher_agent.Task")
    @patch("agents.researcher_agent.Agent")
    @patch("agents.researcher_agent.LLM")
    @patch("agents.researcher_agent.ddg_search")
    def test_uses_topic_in_query(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output_file, sample_articles
    ):
        mock_ddg.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(sample_articles)
        mock_output_file.parent.mkdir = MagicMock()
        mock_output_file.write_text = MagicMock()

        from agents.researcher_agent import fetch_latest_ai_concepts

        output = fetch_latest_ai_concepts(topic="multimodal LLMs")

        assert output["topic"] == "multimodal LLMs"
        # DDG query should have prepended the topic
        first_call_args = mock_ddg.call_args_list[0][0][0]
        assert "multimodal LLMs" in first_call_args

    @patch("agents.researcher_agent.OUTPUT_FILE")
    @patch("agents.researcher_agent.Crew")
    @patch("agents.researcher_agent.Task")
    @patch("agents.researcher_agent.Agent")
    @patch("agents.researcher_agent.LLM")
    @patch("agents.researcher_agent.ddg_search")
    def test_no_topic_defaults_to_latest_ai_updates(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output_file, sample_articles
    ):
        mock_ddg.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(sample_articles)
        mock_output_file.parent.mkdir = MagicMock()
        mock_output_file.write_text = MagicMock()

        from agents.researcher_agent import fetch_latest_ai_concepts

        output = fetch_latest_ai_concepts()

        assert output["topic"] == "Latest AI updates"

    @patch("agents.researcher_agent.OUTPUT_FILE")
    @patch("agents.researcher_agent.Crew")
    @patch("agents.researcher_agent.Task")
    @patch("agents.researcher_agent.Agent")
    @patch("agents.researcher_agent.LLM")
    @patch("agents.researcher_agent.ddg_search")
    def test_falls_back_to_raw_articles_when_json_parse_fails(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output_file
    ):
        mock_ddg.return_value = [{"title": "t", "body": "s", "href": "http://x.com"}]

        bad_result = MagicMock()
        bad_result.__str__ = lambda self: "Not valid JSON at all"
        mock_crew_cls.return_value.kickoff.return_value = bad_result
        mock_output_file.parent.mkdir = MagicMock()
        mock_output_file.write_text = MagicMock()

        from agents.researcher_agent import fetch_latest_ai_concepts

        output = fetch_latest_ai_concepts()

        # Falls back to raw DDG results — should still have articles
        assert isinstance(output["articles"], list)

    @patch("agents.researcher_agent.OUTPUT_FILE")
    @patch("agents.researcher_agent.Crew")
    @patch("agents.researcher_agent.Task")
    @patch("agents.researcher_agent.Agent")
    @patch("agents.researcher_agent.LLM")
    @patch("agents.researcher_agent.ddg_search")
    def test_writes_output_file(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output_file, sample_articles
    ):
        mock_ddg.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(sample_articles)
        mock_output_file.parent.mkdir = MagicMock()
        mock_output_file.write_text = MagicMock()

        from agents.researcher_agent import fetch_latest_ai_concepts

        fetch_latest_ai_concepts()

        mock_output_file.write_text.assert_called_once()
        written = mock_output_file.write_text.call_args[0][0]
        parsed = json.loads(written)
        assert "articles" in parsed
        assert "timestamp" in parsed

    @patch("agents.researcher_agent.OUTPUT_FILE")
    @patch("agents.researcher_agent.Crew")
    @patch("agents.researcher_agent.Task")
    @patch("agents.researcher_agent.Agent")
    @patch("agents.researcher_agent.LLM")
    @patch("agents.researcher_agent.ddg_search")
    def test_sources_searched_matches_all_searches(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output_file, sample_articles
    ):
        mock_ddg.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(sample_articles)
        mock_output_file.parent.mkdir = MagicMock()
        mock_output_file.write_text = MagicMock()

        import agents.researcher_agent as ra
        from agents.researcher_agent import fetch_latest_ai_concepts

        output = fetch_latest_ai_concepts()

        expected_labels = [s["label"] for s in ra.ALL_SEARCHES]
        assert output["sources_searched"] == expected_labels
