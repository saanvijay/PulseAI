"""
Unit tests for Agent 4: Publisher Agent.

The publisher reads the synthesizer output and displays the final article.
No email or LinkedIn functionality — display only.
Mocks:
  - INPUT_FILE.read_text  — synthesizer_output.json
  - OUTPUT_FILE.write_text — publisher_output.json
"""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestPublishResults:
    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    def test_returns_correct_schema(self, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()

        from agents.publisher_agent import publish_results

        result = publish_results()

        assert "timestamp" in result
        assert "final_article" in result
        assert "status" in result

    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    def test_final_article_matches_input_summary(self, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()

        from agents.publisher_agent import publish_results

        result = publish_results()

        assert result["final_article"] == synthesizer_output["final_summary"]

    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    def test_status_is_displayed(self, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()

        from agents.publisher_agent import publish_results

        result = publish_results()

        assert result["status"] == "displayed"

    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    def test_writes_output_file(self, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()

        from agents.publisher_agent import publish_results

        publish_results()

        mock_output.write_text.assert_called_once()
        written = mock_output.write_text.call_args[0][0]
        parsed = json.loads(written)
        assert "timestamp" in parsed
        assert "final_article" in parsed
        assert "status" in parsed

    @patch("agents.publisher_agent.INPUT_FILE")
    def test_raises_when_input_file_missing(self, mock_input):
        mock_input.read_text.side_effect = FileNotFoundError("synthesizer_output.json not found")

        from agents.publisher_agent import publish_results

        with pytest.raises(FileNotFoundError):
            publish_results()
