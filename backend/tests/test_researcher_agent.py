"""
Unit tests for Agent 1: Researcher Agent.

The researcher now fetches articles via Google News RSS (no LLM involved).
Mocks:
  - requests.get              — Google News RSS HTTP calls
  - search_batch_parallel     — batch parallel source search
  - scrape_articles_parallel  — full content scraping
  - OUTPUT_FILE               — file output
"""

import json
from unittest.mock import MagicMock, patch

# ── Sample RSS XML ─────────────────────────────────────────────────────────────

SAMPLE_RSS_XML = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b"<rss><channel>"
    b"<item><title>Claude 3.5 Sonnet Released</title>"
    b"<description>Anthropic releases new model.</description>"
    b"<link>https://anthropic.com/claude-3-5</link>"
    b"<pubDate>Mon, 07 Apr 2026 12:00:00 GMT</pubDate></item>"
    b"<item><title>GPT-5 Coding Benchmarks</title>"
    b"<description>OpenAI GPT-5 achieves top scores.</description>"
    b"<link>https://openai.com/gpt-5</link>"
    b"<pubDate>Mon, 07 Apr 2026 10:00:00 GMT</pubDate></item>"
    b"</channel></rss>"
)


def _make_http_response(xml: bytes = SAMPLE_RSS_XML):
    mock_resp = MagicMock()
    mock_resp.content = xml
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ── gnews_search ──────────────────────────────────────────────────────────────


class TestGnewsSearch:
    SOURCE = {"query": "AI news", "label": "Test Source", "category": "news"}

    def test_returns_articles_on_success(self):
        with patch("agents.researcher_agent.requests.get", return_value=_make_http_response()):
            from agents.researcher_agent import gnews_search

            _src, articles = gnews_search(self.SOURCE, "", max_results=2)

        assert isinstance(articles, list)
        assert len(articles) == 2
        assert articles[0]["title"] == "Claude 3.5 Sonnet Released"

    def test_returns_empty_list_on_exception(self):
        with patch("agents.researcher_agent.requests.get", side_effect=Exception("network error")):
            with patch("agents.researcher_agent.time.sleep"):
                from agents.researcher_agent import gnews_search

                _src, articles = gnews_search(self.SOURCE, "", max_results=2)

        assert articles == []

    def test_returns_source_unchanged_in_tuple(self):
        with patch("agents.researcher_agent.requests.get", return_value=_make_http_response()):
            from agents.researcher_agent import gnews_search

            returned_src, _articles = gnews_search(self.SOURCE, "")

        assert returned_src == self.SOURCE

    def test_article_fields_populated(self):
        with patch("agents.researcher_agent.requests.get", return_value=_make_http_response()):
            from agents.researcher_agent import gnews_search

            _src, articles = gnews_search(self.SOURCE, "")

        a = articles[0]
        assert a["title"] == "Claude 3.5 Sonnet Released"
        assert a["source"] == "Test Source"
        assert a["category"] == "news"
        assert "link" in a


# ── fetch_latest_ai_concepts ──────────────────────────────────────────────────

SAMPLE_ARTICLES = [
    {
        "title": "Claude 3.5 Sonnet",
        "snippet": "AI news",
        "link": "http://a.com",
        "source": "Src",
        "category": "news",
        "date": None,
    },
    {
        "title": "GPT-5",
        "snippet": "More AI",
        "link": "http://b.com",
        "source": "Src2",
        "category": "news",
        "date": None,
    },
    {
        "title": "Gemini Ultra",
        "snippet": "Google AI",
        "link": "http://c.com",
        "source": "Src3",
        "category": "research",
        "date": None,
    },
]


class TestFetchLatestAiConcepts:
    @patch("agents.researcher_agent.OUTPUT_FILE")
    @patch("agents.researcher_agent.scrape_articles_parallel")
    @patch("agents.researcher_agent.search_batch_parallel")
    def test_returns_correct_schema(self, mock_search, mock_scrape, mock_output_file):
        mock_search.return_value = SAMPLE_ARTICLES
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
    @patch("agents.researcher_agent.scrape_articles_parallel")
    @patch("agents.researcher_agent.search_batch_parallel")
    def test_uses_topic(self, mock_search, mock_scrape, mock_output_file):
        mock_search.return_value = SAMPLE_ARTICLES
        mock_output_file.parent.mkdir = MagicMock()
        mock_output_file.write_text = MagicMock()

        from agents.researcher_agent import fetch_latest_ai_concepts

        output = fetch_latest_ai_concepts(topic="multimodal LLMs")

        assert output["topic"] == "multimodal LLMs"

    @patch("agents.researcher_agent.OUTPUT_FILE")
    @patch("agents.researcher_agent.scrape_articles_parallel")
    @patch("agents.researcher_agent.search_batch_parallel")
    def test_no_topic_defaults_to_latest_ai_updates(self, mock_search, mock_scrape, mock_output_file):
        mock_search.return_value = SAMPLE_ARTICLES
        mock_output_file.parent.mkdir = MagicMock()
        mock_output_file.write_text = MagicMock()

        from agents.researcher_agent import fetch_latest_ai_concepts

        output = fetch_latest_ai_concepts()

        assert output["topic"] == "Latest AI updates"

    @patch("agents.researcher_agent.OUTPUT_FILE")
    @patch("agents.researcher_agent.scrape_articles_parallel")
    @patch("agents.researcher_agent.search_batch_parallel")
    def test_deduplicates_articles_by_link(self, mock_search, mock_scrape, mock_output_file):
        duplicate = {
            "title": "AI news",
            "snippet": "s",
            "link": "http://a.com",
            "source": "S",
            "category": "news",
            "date": None,
        }
        mock_search.return_value = [duplicate, duplicate, duplicate]
        mock_output_file.parent.mkdir = MagicMock()
        mock_output_file.write_text = MagicMock()

        from agents.researcher_agent import fetch_latest_ai_concepts

        output = fetch_latest_ai_concepts()

        assert output["total"] == 1

    @patch("agents.researcher_agent.OUTPUT_FILE")
    @patch("agents.researcher_agent.scrape_articles_parallel")
    @patch("agents.researcher_agent.search_batch_parallel")
    def test_writes_output_file(self, mock_search, mock_scrape, mock_output_file):
        mock_search.return_value = SAMPLE_ARTICLES
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
    @patch("agents.researcher_agent.scrape_articles_parallel")
    @patch("agents.researcher_agent.search_batch_parallel")
    def test_sources_searched_is_list_of_labels(self, mock_search, mock_scrape, mock_output_file):
        mock_search.return_value = SAMPLE_ARTICLES
        mock_output_file.parent.mkdir = MagicMock()
        mock_output_file.write_text = MagicMock()

        from agents.researcher_agent import fetch_latest_ai_concepts

        output = fetch_latest_ai_concepts()

        assert isinstance(output["sources_searched"], list)
        assert len(output["sources_searched"]) > 0
        assert all(isinstance(label, str) for label in output["sources_searched"])
