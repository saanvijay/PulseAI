"""
Unit tests for the Trend Agent.

Mocks:
  - DDGS().text()        — DuckDuckGo search
  - crewai.Crew.kickoff  — Ollama / CrewAI pipeline
  - OUTPUT_FILE.write_text — trend_output.json
"""

import json
from unittest.mock import MagicMock, patch

import pytest


# ── ddg_search ────────────────────────────────────────────────────────────────

class TestTrendDdgSearch:
    def test_returns_results_on_success(self, ddg_raw_results):
        with patch("agents.trend_agent.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = ddg_raw_results
            from agents.trend_agent import ddg_search
            result = ddg_search("AI trends", max_results=2)

        assert len(result) == 2
        assert result[0]["title"] == "Claude 3.5 Sonnet Released"

    def test_returns_empty_list_on_exception(self):
        with patch("agents.trend_agent.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.side_effect = RuntimeError("timeout")
            from agents.trend_agent import ddg_search
            result = ddg_search("AI trends")

        assert result == []

    def test_passes_correct_max_results(self, ddg_raw_results):
        with patch("agents.trend_agent.DDGS") as mock_ddgs:
            mock_ctx = mock_ddgs.return_value.__enter__.return_value
            mock_ctx.text.return_value = ddg_raw_results
            from agents.trend_agent import ddg_search
            ddg_search("query", max_results=3)

        mock_ctx.text.assert_called_once_with("query", max_results=3)


# ── get_trending_topic ────────────────────────────────────────────────────────

class TestGetTrendingTopic:
    def _make_crew_result(self, topic: str):
        mock_result = MagicMock()
        mock_result.__str__ = lambda self: topic
        return mock_result

    @patch("agents.trend_agent.OUTPUT_FILE")
    @patch("agents.trend_agent.Crew")
    @patch("agents.trend_agent.Task")
    @patch("agents.trend_agent.Agent")
    @patch("agents.trend_agent.LLM")
    @patch("agents.trend_agent.ddg_search")
    def test_returns_correct_schema(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output
    ):
        mock_ddg.return_value = [{"title": "LLM reasoning advances", "body": "", "href": ""}]
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(
            "LLM reasoning and planning"
        )
        mock_output.parent.mkdir = MagicMock()
        mock_output.write_text = MagicMock()

        from agents.trend_agent import get_trending_topic
        result = get_trending_topic()

        assert "timestamp" in result
        assert "topic" in result
        assert "sources_scanned" in result

    @patch("agents.trend_agent.OUTPUT_FILE")
    @patch("agents.trend_agent.Crew")
    @patch("agents.trend_agent.Task")
    @patch("agents.trend_agent.Agent")
    @patch("agents.trend_agent.LLM")
    @patch("agents.trend_agent.ddg_search")
    def test_topic_is_stripped_of_quotes(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output
    ):
        mock_ddg.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(
            '"Multimodal foundation models"'
        )
        mock_output.parent.mkdir = MagicMock()
        mock_output.write_text = MagicMock()

        from agents.trend_agent import get_trending_topic
        result = get_trending_topic()

        assert result["topic"] == "Multimodal foundation models"
        assert not result["topic"].startswith('"')
        assert not result["topic"].endswith('"')

    @patch("agents.trend_agent.OUTPUT_FILE")
    @patch("agents.trend_agent.Crew")
    @patch("agents.trend_agent.Task")
    @patch("agents.trend_agent.Agent")
    @patch("agents.trend_agent.LLM")
    @patch("agents.trend_agent.ddg_search")
    def test_sources_scanned_is_non_empty(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output
    ):
        mock_ddg.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result("AI agents")
        mock_output.parent.mkdir = MagicMock()
        mock_output.write_text = MagicMock()

        from agents.trend_agent import get_trending_topic
        result = get_trending_topic()

        assert isinstance(result["sources_scanned"], list)
        assert len(result["sources_scanned"]) > 0

    @patch("agents.trend_agent.OUTPUT_FILE")
    @patch("agents.trend_agent.Crew")
    @patch("agents.trend_agent.Task")
    @patch("agents.trend_agent.Agent")
    @patch("agents.trend_agent.LLM")
    @patch("agents.trend_agent.ddg_search")
    def test_writes_output_file(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output
    ):
        mock_ddg.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result("AI agents")
        mock_output.parent.mkdir = MagicMock()
        mock_output.write_text = MagicMock()

        from agents.trend_agent import get_trending_topic
        get_trending_topic()

        mock_output.write_text.assert_called_once()
        written = mock_output.write_text.call_args[0][0]
        parsed = json.loads(written)
        assert "topic" in parsed
        assert "timestamp" in parsed

    @patch("agents.trend_agent.OUTPUT_FILE")
    @patch("agents.trend_agent.Crew")
    @patch("agents.trend_agent.Task")
    @patch("agents.trend_agent.Agent")
    @patch("agents.trend_agent.LLM")
    @patch("agents.trend_agent.ddg_search")
    def test_handles_no_search_results_gracefully(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output
    ):
        mock_ddg.return_value = []  # All searches return nothing
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(
            "retrieval augmented generation"
        )
        mock_output.parent.mkdir = MagicMock()
        mock_output.write_text = MagicMock()

        from agents.trend_agent import get_trending_topic
        result = get_trending_topic()

        # Should still run and return a topic from Ollama
        assert isinstance(result["topic"], str)
        assert len(result["topic"]) > 0

    @patch("agents.trend_agent.OUTPUT_FILE")
    @patch("agents.trend_agent.Crew")
    @patch("agents.trend_agent.Task")
    @patch("agents.trend_agent.Agent")
    @patch("agents.trend_agent.LLM")
    @patch("agents.trend_agent.ddg_search")
    def test_crew_kickoff_called_once(
        self, mock_ddg, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_output
    ):
        mock_ddg.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result("AI safety")
        mock_output.parent.mkdir = MagicMock()
        mock_output.write_text = MagicMock()

        from agents.trend_agent import get_trending_topic
        get_trending_topic()

        mock_crew_cls.return_value.kickoff.assert_called_once()
