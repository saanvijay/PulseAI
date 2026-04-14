"""
Unit tests for Agent 2: Analyst Agent.

Mocks:
  - INPUT_FILE.read_text  — researcher_output.json
  - OUTPUT_FILE.write_text — analyst_output.json
  - crewai.Crew.kickoff   — Ollama / CrewAI pipeline
"""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestOrganizeContent:
    def _make_crew_result(self, report_text: str):
        mock_result = MagicMock()
        mock_result.__str__ = lambda self: report_text
        return mock_result

    SAMPLE_REPORT = (
        "## 1. Introduction\nLatest AI trends.\n\n"
        "## 2. Existing Problems\nHallucination.\n\n"
        "## 3. Proposed Solutions\nRLHF.\n\n"
        "## 4. Architecture Overview\n[LLM]-->[Output]\n\n"
        "## 5. Advantages\nFaster inference.\n\n"
        "## 6. Disadvantages\nHigh cost.\n\n"
        "## 7. Applied AI Use Cases\nCode, summarization.\n\n"
        "## 8. Future Implementation\nMultimodal agents."
    )

    # Patch Agent and Task alongside Crew/LLM to bypass Pydantic validation
    @patch("agents.analyst_agent.OUTPUT_FILE")
    @patch("agents.analyst_agent.INPUT_FILE")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.analyst_agent.LLM")
    def test_returns_correct_schema(
        self, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_input, mock_output, researcher_output
    ):
        mock_input.read_text.return_value = json.dumps(researcher_output)
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(self.SAMPLE_REPORT)
        mock_output.write_text = MagicMock()

        from agents.analyst_agent import organize_content

        result = organize_content()

        assert "timestamp" in result
        assert "source_articles" in result
        assert "report" in result

    @patch("agents.analyst_agent.OUTPUT_FILE")
    @patch("agents.analyst_agent.INPUT_FILE")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.analyst_agent.LLM")
    def test_source_articles_count_matches_input(
        self, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_input, mock_output, researcher_output
    ):
        mock_input.read_text.return_value = json.dumps(researcher_output)
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(self.SAMPLE_REPORT)
        mock_output.write_text = MagicMock()

        from agents.analyst_agent import organize_content

        result = organize_content()

        assert result["source_articles"] == len(researcher_output["articles"])

    @patch("agents.analyst_agent.OUTPUT_FILE")
    @patch("agents.analyst_agent.INPUT_FILE")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.analyst_agent.LLM")
    def test_report_is_string(
        self, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_input, mock_output, researcher_output
    ):
        mock_input.read_text.return_value = json.dumps(researcher_output)
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(self.SAMPLE_REPORT)
        mock_output.write_text = MagicMock()

        from agents.analyst_agent import organize_content

        result = organize_content()

        assert isinstance(result["report"], str)
        assert len(result["report"]) > 0

    @patch("agents.analyst_agent.OUTPUT_FILE")
    @patch("agents.analyst_agent.INPUT_FILE")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.analyst_agent.LLM")
    def test_writes_output_file(
        self, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_input, mock_output, researcher_output
    ):
        mock_input.read_text.return_value = json.dumps(researcher_output)
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(self.SAMPLE_REPORT)
        mock_output.write_text = MagicMock()

        from agents.analyst_agent import organize_content

        organize_content()

        mock_output.write_text.assert_called_once()
        written = mock_output.write_text.call_args[0][0]
        parsed = json.loads(written)
        assert "report" in parsed
        assert "source_articles" in parsed

    @patch("agents.analyst_agent.OUTPUT_FILE")
    @patch("agents.analyst_agent.INPUT_FILE")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.analyst_agent.LLM")
    def test_crew_kickoff_is_called_once(
        self, mock_llm, mock_agent, mock_task, mock_crew_cls, mock_input, mock_output, researcher_output
    ):
        mock_input.read_text.return_value = json.dumps(researcher_output)
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(self.SAMPLE_REPORT)
        mock_output.write_text = MagicMock()

        from agents.analyst_agent import organize_content

        organize_content()

        mock_crew_cls.return_value.kickoff.assert_called_once()

    @patch("agents.analyst_agent.INPUT_FILE")
    def test_raises_when_input_file_missing(self, mock_input):
        mock_input.read_text.side_effect = FileNotFoundError("researcher_output.json not found")

        from agents.analyst_agent import organize_content

        with pytest.raises(FileNotFoundError):
            organize_content()
