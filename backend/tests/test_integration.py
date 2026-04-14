"""
Integration test for the PulseAI multi-agent pipeline.

Tests the full pipeline end-to-end with all external services mocked:
  - DuckDuckGo searches
  - Ollama / CrewAI (LLM, Agent, Task, Crew)
  - Ollama direct API (synthesizer per-model calls)
  - Gmail SMTP
  - LinkedIn API
  - File I/O (uses tmp_path to avoid touching the real output/ directory)

The integration test verifies:
  1. Agents run in the correct sequence (researcher → analyst → synthesizer → publisher)
  2. Data flows correctly between agents via JSON files
  3. Each agent produces the expected output schema
  4. The orchestrator wires everything together correctly
"""

import json
import os
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


# CrewAI patch targets for each module (Agent + Task + Crew + LLM)
_RESEARCHER_PATCHES = [
    "agents.researcher_agent.Agent",
    "agents.researcher_agent.Task",
    "agents.researcher_agent.Crew",
    "agents.researcher_agent.LLM",
    "agents.researcher_agent.ddg_search",
]
_ANALYST_PATCHES = [
    "agents.analyst_agent.Agent",
    "agents.analyst_agent.Task",
    "agents.analyst_agent.Crew",
    "agents.analyst_agent.LLM",
]
_SYNTH_PATCHES = [
    "agents.synthesizer_agent.Agent",
    "agents.synthesizer_agent.Task",
    "agents.synthesizer_agent.Crew",
    "agents.synthesizer_agent.LLM",
    "agents.synthesizer_agent.requests.post",
]


# ── Integration: Full pipeline ────────────────────────────────────────────────


class TestFullPipeline:
    def _setup_mocks(
        self,
        mock_ddg,
        mock_researcher_agent,
        mock_researcher_task,
        mock_researcher_crew,
        mock_researcher_llm,
        mock_analyst_agent,
        mock_analyst_task,
        mock_analyst_crew,
        mock_analyst_llm,
        mock_synth_agent,
        mock_synth_task,
        mock_synth_crew,
        mock_synth_llm,
        mock_synth_post,
    ):
        mock_ddg.return_value = [{"title": "t", "body": "s", "href": "http://x.com"}]
        mock_researcher_crew.return_value.kickoff.return_value = _make_crew_result(json.dumps(SAMPLE_ARTICLES))
        mock_analyst_crew.return_value.kickoff.return_value = _make_crew_result(SAMPLE_REPORT)
        mock_synth_post.return_value = _make_ollama_response("Key insight.")
        mock_synth_crew.return_value.kickoff.return_value = _make_crew_result(FINAL_SUMMARY)

    @patch("agents.synthesizer_agent.requests.post")
    @patch("agents.synthesizer_agent.LLM")
    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.analyst_agent.LLM")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.researcher_agent.ddg_search")
    @patch("agents.researcher_agent.LLM")
    @patch("agents.researcher_agent.Crew")
    @patch("agents.researcher_agent.Task")
    @patch("agents.researcher_agent.Agent")
    def test_pipeline_runs_all_four_agents(
        self,
        mock_r_agent,
        mock_r_task,
        mock_r_crew,
        mock_r_llm,
        mock_ddg,
        mock_a_agent,
        mock_a_task,
        mock_a_crew,
        mock_a_llm,
        mock_s_agent,
        mock_s_task,
        mock_s_crew,
        mock_s_llm,
        mock_s_post,
        tmp_path,
        monkeypatch,
    ):
        r_out, a_out, s_out, p_out = _patch_agent_files(tmp_path, monkeypatch)
        for key in ("EMAIL_USER", "EMAIL_PASS", "EMAIL_TO", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_ID"):
            os.environ.pop(key, None)

        mock_ddg.return_value = [{"title": "t", "body": "s", "href": "http://x.com"}]
        mock_r_crew.return_value.kickoff.return_value = _make_crew_result(json.dumps(SAMPLE_ARTICLES))
        mock_a_crew.return_value.kickoff.return_value = _make_crew_result(SAMPLE_REPORT)
        mock_s_post.return_value = _make_ollama_response("Insight.")
        mock_s_crew.return_value.kickoff.return_value = _make_crew_result(FINAL_SUMMARY)

        from orchestrator import run_pipeline

        run_pipeline()

        assert r_out.exists(), "researcher_output.json was not created"
        assert a_out.exists(), "analyst_output.json was not created"
        assert s_out.exists(), "synthesizer_output.json was not created"
        assert p_out.exists(), "publisher_output.json was not created"

    @patch("agents.synthesizer_agent.requests.post")
    @patch("agents.synthesizer_agent.LLM")
    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.analyst_agent.LLM")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.researcher_agent.ddg_search")
    @patch("agents.researcher_agent.LLM")
    @patch("agents.researcher_agent.Crew")
    @patch("agents.researcher_agent.Task")
    @patch("agents.researcher_agent.Agent")
    def test_data_flows_correctly_between_agents(
        self,
        mock_r_agent,
        mock_r_task,
        mock_r_crew,
        mock_r_llm,
        mock_ddg,
        mock_a_agent,
        mock_a_task,
        mock_a_crew,
        mock_a_llm,
        mock_s_agent,
        mock_s_task,
        mock_s_crew,
        mock_s_llm,
        mock_s_post,
        tmp_path,
        monkeypatch,
    ):
        r_out, a_out, s_out, p_out = _patch_agent_files(tmp_path, monkeypatch)
        for key in ("EMAIL_USER", "EMAIL_PASS", "EMAIL_TO", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_ID"):
            os.environ.pop(key, None)

        mock_ddg.return_value = [{"title": "t", "body": "s", "href": "http://x.com"}]
        mock_r_crew.return_value.kickoff.return_value = _make_crew_result(json.dumps(SAMPLE_ARTICLES))
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
        assert "linkedin_post_preview" in p_data
        assert FINAL_SUMMARY in p_data["linkedin_post_preview"]

    @patch("agents.synthesizer_agent.requests.post")
    @patch("agents.synthesizer_agent.LLM")
    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.analyst_agent.LLM")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.researcher_agent.ddg_search")
    @patch("agents.researcher_agent.LLM")
    @patch("agents.researcher_agent.Crew")
    @patch("agents.researcher_agent.Task")
    @patch("agents.researcher_agent.Agent")
    def test_pipeline_output_schemas_are_valid(
        self,
        mock_r_agent,
        mock_r_task,
        mock_r_crew,
        mock_r_llm,
        mock_ddg,
        mock_a_agent,
        mock_a_task,
        mock_a_crew,
        mock_a_llm,
        mock_s_agent,
        mock_s_task,
        mock_s_crew,
        mock_s_llm,
        mock_s_post,
        tmp_path,
        monkeypatch,
    ):
        r_out, a_out, s_out, p_out = _patch_agent_files(tmp_path, monkeypatch)
        for key in ("EMAIL_USER", "EMAIL_PASS", "EMAIL_TO", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_ID"):
            os.environ.pop(key, None)

        mock_ddg.return_value = [{"title": "t", "body": "s", "href": "http://x.com"}]
        mock_r_crew.return_value.kickoff.return_value = _make_crew_result(json.dumps(SAMPLE_ARTICLES))
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
        assert all(k in p for k in ("timestamp", "email", "linkedin", "linkedin_post_preview"))
        assert "status" in p["email"]
        assert "status" in p["linkedin"]

    @patch("agents.synthesizer_agent.requests.post")
    @patch("agents.synthesizer_agent.LLM")
    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.analyst_agent.LLM")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.researcher_agent.ddg_search")
    @patch("agents.researcher_agent.LLM")
    @patch("agents.researcher_agent.Crew")
    @patch("agents.researcher_agent.Task")
    @patch("agents.researcher_agent.Agent")
    def test_pipeline_with_topic_argument(
        self,
        mock_r_agent,
        mock_r_task,
        mock_r_crew,
        mock_r_llm,
        mock_ddg,
        mock_a_agent,
        mock_a_task,
        mock_a_crew,
        mock_a_llm,
        mock_s_agent,
        mock_s_task,
        mock_s_crew,
        mock_s_llm,
        mock_s_post,
        tmp_path,
        monkeypatch,
    ):
        r_out, a_out, s_out, p_out = _patch_agent_files(tmp_path, monkeypatch)
        for key in ("EMAIL_USER", "EMAIL_PASS", "EMAIL_TO", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_ID"):
            os.environ.pop(key, None)

        mock_ddg.return_value = []
        mock_r_crew.return_value.kickoff.return_value = _make_crew_result(json.dumps(SAMPLE_ARTICLES))
        mock_a_crew.return_value.kickoff.return_value = _make_crew_result(SAMPLE_REPORT)
        mock_s_post.return_value = _make_ollama_response("Insight.")
        mock_s_crew.return_value.kickoff.return_value = _make_crew_result(FINAL_SUMMARY)

        from orchestrator import run_pipeline

        run_pipeline(topic="agentic AI systems")

        r = json.loads(r_out.read_text())
        assert r["topic"] == "agentic AI systems"

    @patch("agents.publisher_agent.post_to_linkedin")
    @patch("agents.publisher_agent.send_email")
    @patch("agents.synthesizer_agent.requests.post")
    @patch("agents.synthesizer_agent.LLM")
    @patch("agents.synthesizer_agent.Crew")
    @patch("agents.synthesizer_agent.Task")
    @patch("agents.synthesizer_agent.Agent")
    @patch("agents.analyst_agent.LLM")
    @patch("agents.analyst_agent.Crew")
    @patch("agents.analyst_agent.Task")
    @patch("agents.analyst_agent.Agent")
    @patch("agents.researcher_agent.ddg_search")
    @patch("agents.researcher_agent.LLM")
    @patch("agents.researcher_agent.Crew")
    @patch("agents.researcher_agent.Task")
    @patch("agents.researcher_agent.Agent")
    def test_pipeline_with_publisher_credentials(
        self,
        mock_r_agent,
        mock_r_task,
        mock_r_crew,
        mock_r_llm,
        mock_ddg,
        mock_a_agent,
        mock_a_task,
        mock_a_crew,
        mock_a_llm,
        mock_s_agent,
        mock_s_task,
        mock_s_crew,
        mock_s_llm,
        mock_s_post,
        mock_send_email,
        mock_post_li,
        tmp_path,
        monkeypatch,
    ):
        r_out, a_out, s_out, p_out = _patch_agent_files(tmp_path, monkeypatch)

        mock_send_email.return_value = {"messageId": "<ts@gmail.com>"}
        mock_post_li.return_value = {"postId": "urn:li:ugcPost:1", "status": 201}

        mock_ddg.return_value = []
        mock_r_crew.return_value.kickoff.return_value = _make_crew_result(json.dumps(SAMPLE_ARTICLES))
        mock_a_crew.return_value.kickoff.return_value = _make_crew_result(SAMPLE_REPORT)
        mock_s_post.return_value = _make_ollama_response("Insight.")
        mock_s_crew.return_value.kickoff.return_value = _make_crew_result(FINAL_SUMMARY)

        env = {
            "EMAIL_USER": "u@g.com",
            "EMAIL_PASS": "pw",
            "EMAIL_TO": "t@g.com",
            "LINKEDIN_ACCESS_TOKEN": "token",
            "LINKEDIN_PERSON_ID": "pid",
        }
        with patch.dict("os.environ", env):
            from orchestrator import run_pipeline

            run_pipeline()

        mock_send_email.assert_called_once()
        mock_post_li.assert_called_once()

        p = json.loads(p_out.read_text())
        assert p["email"]["status"] == "success"
        # post_to_linkedin returns {"postId": ..., "status": 201}; 201 overwrites "success"
        assert p["linkedin"]["postId"] == "urn:li:ugcPost:1"

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
