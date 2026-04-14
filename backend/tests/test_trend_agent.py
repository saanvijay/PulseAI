"""
Unit tests for the Trend Agent.

The trend agent fetches headlines via Google News RSS and uses a local
Ollama model (via CrewAI) to identify the top 5 trending AI topics.
Mocks:
  - requests.get              — Google News RSS HTTP calls
  - search_sources_parallel   — parallel headline collection
  - get_llm                   — LLM factory (prevents real Ollama calls)
  - crewai.Crew.kickoff       — Ollama / CrewAI pipeline
  - OUTPUT_FILE.write_text    — trend_output.json
"""

import json
from unittest.mock import MagicMock, patch

SAMPLE_RSS_XML = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b"<rss><channel>"
    b"<item><title>Claude 3.5 Sonnet Released</title>"
    b"<source>Anthropic</source></item>"
    b"<item><title>GPT-5 Coding Benchmarks</title>"
    b"<source>OpenAI</source></item>"
    b"</channel></rss>"
)

NUMBERED_TOPICS = (
    "1. LLM reasoning and planning\n"
    "2. Multimodal foundation models\n"
    "3. AI agents and autonomy\n"
    "4. Retrieval-augmented generation\n"
    "5. Open-source model releases"
)


def _make_http_response(xml: bytes = SAMPLE_RSS_XML):
    mock_resp = MagicMock()
    mock_resp.content = xml
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ── gnews_search ──────────────────────────────────────────────────────────────


class TestGnewsSearch:
    SOURCE = {"query": "AI trends", "label": "Test Source", "category": "news"}

    def test_returns_results_on_success(self):
        with patch("agents.trend_agent.requests.get", return_value=_make_http_response()):
            from agents.trend_agent import gnews_search

            _src, results = gnews_search(self.SOURCE, max_results=2)

        assert len(results) == 2
        assert results[0]["title"] == "Claude 3.5 Sonnet Released"

    def test_returns_empty_list_on_exception(self):
        with patch("agents.trend_agent.requests.get", side_effect=RuntimeError("timeout")):
            from agents.trend_agent import gnews_search

            _src, results = gnews_search(self.SOURCE, max_results=2)

        assert results == []

    def test_returns_source_in_tuple(self):
        with patch("agents.trend_agent.requests.get", return_value=_make_http_response()):
            from agents.trend_agent import gnews_search

            returned_src, _results = gnews_search(self.SOURCE, max_results=3)

        assert returned_src == self.SOURCE


# ── get_trending_topic ────────────────────────────────────────────────────────


class TestGetTrendingTopic:
    def _make_crew_result(self, text: str):
        mock_result = MagicMock()
        mock_result.__str__ = lambda self: text
        return mock_result

    @patch("agents.trend_agent.OUTPUT_FILE")
    @patch("agents.trend_agent.Crew")
    @patch("agents.trend_agent.Task")
    @patch("agents.trend_agent.Agent")
    @patch("agents.trend_agent.get_llm")
    @patch("agents.trend_agent.search_sources_parallel")
    def test_returns_correct_schema(self, mock_search, mock_get_llm, mock_agent, mock_task, mock_crew_cls, mock_output):
        mock_search.return_value = ["- LLM news (Source1)"]
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(NUMBERED_TOPICS)
        mock_output.parent.mkdir = MagicMock()
        mock_output.write_text = MagicMock()

        from agents.trend_agent import get_trending_topic

        result = get_trending_topic()

        assert "timestamp" in result
        assert "topic" in result
        assert "topics" in result
        assert "sources_scanned" in result

    @patch("agents.trend_agent.OUTPUT_FILE")
    @patch("agents.trend_agent.Crew")
    @patch("agents.trend_agent.Task")
    @patch("agents.trend_agent.Agent")
    @patch("agents.trend_agent.get_llm")
    @patch("agents.trend_agent.search_sources_parallel")
    def test_topic_is_stripped_of_quotes(
        self, mock_search, mock_get_llm, mock_agent, mock_task, mock_crew_cls, mock_output
    ):
        mock_search.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(
            '1. "Multimodal foundation models"\n2. AI agents'
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
    @patch("agents.trend_agent.get_llm")
    @patch("agents.trend_agent.search_sources_parallel")
    def test_sources_scanned_is_non_empty(
        self, mock_search, mock_get_llm, mock_agent, mock_task, mock_crew_cls, mock_output
    ):
        mock_search.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(NUMBERED_TOPICS)
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
    @patch("agents.trend_agent.get_llm")
    @patch("agents.trend_agent.search_sources_parallel")
    def test_writes_output_file(self, mock_search, mock_get_llm, mock_agent, mock_task, mock_crew_cls, mock_output):
        mock_search.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(NUMBERED_TOPICS)
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
    @patch("agents.trend_agent.get_llm")
    @patch("agents.trend_agent.search_sources_parallel")
    def test_handles_no_search_results_gracefully(
        self, mock_search, mock_get_llm, mock_agent, mock_task, mock_crew_cls, mock_output
    ):
        mock_search.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(
            "1. retrieval augmented generation"
        )
        mock_output.parent.mkdir = MagicMock()
        mock_output.write_text = MagicMock()

        from agents.trend_agent import get_trending_topic

        result = get_trending_topic()

        assert isinstance(result["topic"], str)
        assert len(result["topic"]) > 0

    @patch("agents.trend_agent.OUTPUT_FILE")
    @patch("agents.trend_agent.Crew")
    @patch("agents.trend_agent.Task")
    @patch("agents.trend_agent.Agent")
    @patch("agents.trend_agent.get_llm")
    @patch("agents.trend_agent.search_sources_parallel")
    def test_crew_kickoff_called_once(
        self, mock_search, mock_get_llm, mock_agent, mock_task, mock_crew_cls, mock_output
    ):
        mock_search.return_value = []
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result("1. AI safety")
        mock_output.parent.mkdir = MagicMock()
        mock_output.write_text = MagicMock()

        from agents.trend_agent import get_trending_topic

        get_trending_topic()

        mock_crew_cls.return_value.kickoff.assert_called_once()
