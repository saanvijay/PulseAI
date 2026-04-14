"""
Unit tests for Agent 3: Synthesizer Agent.

Mocks:
  - requests.post         — direct Ollama /api/generate calls
  - crewai.Crew.kickoff   — final consolidation via CrewAI
  - INPUT_FILE.read_text  — analyst_output.json
  - OUTPUT_FILE.write_text — synthesizer_output.json
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# ── ask_ollama ────────────────────────────────────────────────────────────────


class TestAskOllama:
    def test_returns_response_text_on_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "LLMs are powerful tools."}
        mock_response.raise_for_status = MagicMock()

        with patch("agents.synthesizer_agent.requests.post", return_value=mock_response):
            from agents.synthesizer_agent import ask_ollama

            result = ask_ollama("llama3.2", "Summarize AI trends.", max_tokens=512)

        assert result == "LLMs are powerful tools."

    def test_raises_on_http_error(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("503 Service Unavailable")

        with patch("agents.synthesizer_agent.requests.post", return_value=mock_response):
            from agents.synthesizer_agent import ask_ollama

            with pytest.raises(Exception, match="503"):
                ask_ollama("llama3.2", "prompt")

    def test_posts_to_correct_endpoint(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "ok"}
        mock_response.raise_for_status = MagicMock()

        with patch("agents.synthesizer_agent.requests.post", return_value=mock_response) as mock_post:
            from agents.synthesizer_agent import ask_ollama

            ask_ollama("mistral", "test prompt")

        call_url = mock_post.call_args[0][0]
        assert "/api/generate" in call_url

    def test_passes_stream_false(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "ok"}
        mock_response.raise_for_status = MagicMock()

        with patch("agents.synthesizer_agent.requests.post", return_value=mock_response) as mock_post:
            from agents.synthesizer_agent import ask_ollama

            ask_ollama("phi3", "test")

        payload = mock_post.call_args[1]["json"]
        assert payload["stream"] is False


# ── call_model ────────────────────────────────────────────────────────────────


class TestCallModel:
    def test_returns_success_dict(self):
        with patch("agents.synthesizer_agent.ask_ollama", return_value="Key insights here."):
            from agents.synthesizer_agent import call_model

            result = call_model("Llama 3.2", "llama3.2", "AI report text")

        assert result["model"] == "Llama 3.2"
        assert result["status"] == "success"
        assert result["summary"] == "Key insights here."
        assert "error" not in result

    def test_returns_error_dict_on_failure(self):
        with patch("agents.synthesizer_agent.ask_ollama", side_effect=Exception("model not found")):
            from agents.synthesizer_agent import call_model

            result = call_model("Phi-3", "phi3", "AI report text")

        assert result["model"] == "Phi-3"
        assert result["status"] == "error"
        assert result["summary"] is None
        assert "model not found" in result["error"]


# ── create_final_summary ──────────────────────────────────────────────────────


class TestCreateFinalSummary:
    def _make_crew_result(self, text: str):
        mock_result = MagicMock()
        mock_result.__str__ = lambda self: text
        return mock_result

    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.synthesizer_agent.get_llm")
    def test_returns_string(self, mock_llm, mock_agent, mock_task, mock_crew_cls):
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result(
            "AI is advancing rapidly with new models from top labs."
        )
        model_responses = [
            {"model": "Llama 3.2", "status": "success", "summary": "Summary 1"},
            {"model": "Mistral", "status": "success", "summary": "Summary 2"},
        ]

        from agents.synthesizer_agent import create_final_summary

        result = create_final_summary("Report text", model_responses)

        assert isinstance(result, str)
        assert len(result) > 0

    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.synthesizer_agent.get_llm")
    def test_skips_failed_models(self, mock_llm, mock_agent, mock_task, mock_crew_cls):
        mock_crew_cls.return_value.kickoff.return_value = self._make_crew_result("Final summary.")
        model_responses = [
            {"model": "Llama 3.2", "status": "success", "summary": "Good summary"},
            {"model": "Phi-3", "status": "error", "summary": None, "error": "timeout"},
        ]

        from agents.synthesizer_agent import create_final_summary

        create_final_summary("Report", model_responses)

        # Verify kickoff was called (means the crew ran)
        mock_crew_cls.return_value.kickoff.assert_called_once()


# ── summarize_with_multiple_models ────────────────────────────────────────────


class TestSummarizeWithMultipleModels:
    def _make_crew_result(self, text: str):
        mock_result = MagicMock()
        mock_result.__str__ = lambda self: text
        return mock_result

    @patch("agents.synthesizer_agent.OUTPUT_FILE")
    @patch("agents.synthesizer_agent.INPUT_FILE")
    @patch("agents.synthesizer_agent.create_final_summary")
    @patch("agents.synthesizer_agent.call_model")
    def test_returns_correct_schema(self, mock_call_model, mock_final, mock_input, mock_output, analyst_output):
        mock_input.read_text.return_value = json.dumps(analyst_output)
        mock_call_model.side_effect = lambda name, model, report, topic="": {"model": name, "status": "success", "summary": "ok"}
        mock_final.return_value = "Consolidated AI summary."
        mock_output.write_text = MagicMock()

        from agents.synthesizer_agent import summarize_with_multiple_models

        result = summarize_with_multiple_models()

        assert "timestamp" in result
        assert "models_queried" in result
        assert "models_successful" in result
        assert "model_responses" in result
        assert "final_summary" in result

    @patch("agents.synthesizer_agent.OUTPUT_FILE")
    @patch("agents.synthesizer_agent.INPUT_FILE")
    @patch("agents.synthesizer_agent.create_final_summary")
    @patch("agents.synthesizer_agent.call_model")
    def test_models_queried_matches_ollama_models_list(
        self, mock_call_model, mock_final, mock_input, mock_output, analyst_output
    ):
        mock_input.read_text.return_value = json.dumps(analyst_output)
        mock_call_model.side_effect = lambda name, model, report, topic="": {"model": name, "status": "success", "summary": "s"}
        mock_final.return_value = "Summary."
        mock_output.write_text = MagicMock()

        import agents.synthesizer_agent as sa
        from agents.synthesizer_agent import summarize_with_multiple_models

        result = summarize_with_multiple_models()

        assert result["models_queried"] == len(sa.OLLAMA_MODELS)

    @patch("agents.synthesizer_agent.OUTPUT_FILE")
    @patch("agents.synthesizer_agent.INPUT_FILE")
    @patch("agents.synthesizer_agent.create_final_summary")
    @patch("agents.synthesizer_agent.call_model")
    def test_counts_only_successful_models(self, mock_call_model, mock_final, mock_input, mock_output, analyst_output):
        mock_input.read_text.return_value = json.dumps(analyst_output)
        # Alternate success and failure
        mock_call_model.side_effect = [
            {"model": "Llama 3.2", "status": "success", "summary": "ok"},
            {"model": "Mistral", "status": "error", "summary": None, "error": "err"},
            {"model": "Qwen 2.5", "status": "success", "summary": "ok"},
            {"model": "Phi-3", "status": "error", "summary": None, "error": "err"},
            {"model": "Gemma 2", "status": "success", "summary": "ok"},
        ]
        mock_final.return_value = "Summary."
        mock_output.write_text = MagicMock()

        from agents.synthesizer_agent import summarize_with_multiple_models

        result = summarize_with_multiple_models()

        assert result["models_successful"] == 3

    @patch("agents.synthesizer_agent.OUTPUT_FILE")
    @patch("agents.synthesizer_agent.INPUT_FILE")
    @patch("agents.synthesizer_agent.create_final_summary")
    @patch("agents.synthesizer_agent.call_model")
    def test_writes_output_file(self, mock_call_model, mock_final, mock_input, mock_output, analyst_output):
        mock_input.read_text.return_value = json.dumps(analyst_output)
        mock_call_model.side_effect = lambda name, model, report, topic="": {"model": name, "status": "success", "summary": "s"}
        mock_final.return_value = "Summary."
        mock_output.write_text = MagicMock()

        from agents.synthesizer_agent import summarize_with_multiple_models

        summarize_with_multiple_models()

        mock_output.write_text.assert_called_once()
        written = mock_output.write_text.call_args[0][0]
        parsed = json.loads(written)
        assert "final_summary" in parsed

    @patch("agents.synthesizer_agent.INPUT_FILE")
    def test_raises_when_input_file_missing(self, mock_input):
        mock_input.read_text.side_effect = FileNotFoundError("analyst_output.json not found")

        from agents.synthesizer_agent import summarize_with_multiple_models

        with pytest.raises(FileNotFoundError):
            summarize_with_multiple_models()
