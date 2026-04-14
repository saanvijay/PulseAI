"""
Unit tests for Agent 4: Publisher Agent.

Mocks:
  - smtplib.SMTP_SSL      — Gmail SMTP connection
  - requests.post         — LinkedIn API
  - INPUT_FILE.read_text  — synthesizer_output.json
  - OUTPUT_FILE.write_text — publisher_output.json
  - os.environ            — email/LinkedIn credentials
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# ── format_linkedin_post ──────────────────────────────────────────────────────


class TestFormatLinkedinPost:
    def test_includes_header(self):
        from agents.publisher_agent import format_linkedin_post

        result = format_linkedin_post("AI is changing the world.")
        assert "🤖 Latest AI Update — Powered by PulseAI" in result

    def test_includes_summary(self):
        from agents.publisher_agent import format_linkedin_post

        summary = "Multimodal models dominate the news this week."
        result = format_linkedin_post(summary)
        assert summary in result

    def test_includes_hashtags(self):
        from agents.publisher_agent import format_linkedin_post

        result = format_linkedin_post("Summary text.")
        assert "#AI" in result
        assert "#MachineLearning" in result
        assert "#GenAI" in result

    def test_header_appears_before_summary(self):
        from agents.publisher_agent import format_linkedin_post

        summary = "The summary."
        result = format_linkedin_post(summary)
        assert result.index("PulseAI") < result.index(summary)


# ── send_email ────────────────────────────────────────────────────────────────


class TestSendEmail:
    @patch("agents.publisher_agent.smtplib.SMTP_SSL")
    def test_returns_message_id_on_success(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        env = {
            "EMAIL_USER": "sender@gmail.com",
            "EMAIL_PASS": "app_password",
            "EMAIL_TO": "recipient@gmail.com",
        }
        with patch.dict("os.environ", env):
            from agents.publisher_agent import send_email

            result = send_email("PulseAI Update", "Great AI news today.")

        assert "messageId" in result
        assert "@gmail.com" in result["messageId"]

    @patch("agents.publisher_agent.smtplib.SMTP_SSL")
    def test_calls_smtp_login_and_sendmail(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        env = {
            "EMAIL_USER": "sender@gmail.com",
            "EMAIL_PASS": "secret",
            "EMAIL_TO": "to@gmail.com",
        }
        with patch.dict("os.environ", env):
            from agents.publisher_agent import send_email

            send_email("Subject", "Body")

        mock_server.login.assert_called_once_with("sender@gmail.com", "secret")
        mock_server.sendmail.assert_called_once()

    @patch("agents.publisher_agent.smtplib.SMTP_SSL")
    def test_raises_on_smtp_error(self, mock_smtp_cls):
        mock_smtp_cls.return_value.__enter__.side_effect = Exception("Connection refused")

        env = {
            "EMAIL_USER": "sender@gmail.com",
            "EMAIL_PASS": "pw",
            "EMAIL_TO": "to@gmail.com",
        }
        with patch.dict("os.environ", env):
            from agents.publisher_agent import send_email

            with pytest.raises(Exception, match="Connection refused"):
                send_email("Subject", "Body")


# ── post_to_linkedin ──────────────────────────────────────────────────────────


class TestPostToLinkedin:
    def test_returns_post_id_on_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "urn:li:ugcPost:123456"}
        mock_response.status_code = 201
        mock_response.raise_for_status = MagicMock()

        env = {
            "LINKEDIN_ACCESS_TOKEN": "token_abc",
            "LINKEDIN_PERSON_ID": "person_xyz",
        }
        with patch("agents.publisher_agent.requests.post", return_value=mock_response):
            with patch.dict("os.environ", env):
                from agents.publisher_agent import post_to_linkedin

                result = post_to_linkedin("AI news content here.")

        assert result["postId"] == "urn:li:ugcPost:123456"
        assert result["status"] == 201

    def test_sends_bearer_token_in_header(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "post_1"}
        mock_response.status_code = 201
        mock_response.raise_for_status = MagicMock()

        env = {
            "LINKEDIN_ACCESS_TOKEN": "my_token",
            "LINKEDIN_PERSON_ID": "person_1",
        }
        with patch("agents.publisher_agent.requests.post", return_value=mock_response) as mock_post:
            with patch.dict("os.environ", env):
                from agents.publisher_agent import post_to_linkedin

                post_to_linkedin("Content")

        headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer my_token"

    def test_raises_on_api_error(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")

        env = {
            "LINKEDIN_ACCESS_TOKEN": "bad_token",
            "LINKEDIN_PERSON_ID": "person_1",
        }
        with patch("agents.publisher_agent.requests.post", return_value=mock_response):
            with patch.dict("os.environ", env):
                from agents.publisher_agent import post_to_linkedin

                with pytest.raises(Exception, match="401"):
                    post_to_linkedin("Content")


# ── publish_results ───────────────────────────────────────────────────────────


class TestPublishResults:
    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    def test_skips_email_when_env_vars_missing(self, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()

        with patch.dict("os.environ", {}, clear=False):
            # Ensure email vars are absent
            import os

            for key in ("EMAIL_USER", "EMAIL_PASS", "EMAIL_TO"):
                os.environ.pop(key, None)

            from agents.publisher_agent import publish_results

            result = publish_results()

        assert result["email"]["status"] == "skipped"

    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    def test_skips_linkedin_when_env_vars_missing(self, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()

        import os

        for key in ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_ID"):
            os.environ.pop(key, None)

        from agents.publisher_agent import publish_results

        result = publish_results()

        assert result["linkedin"]["status"] == "skipped"

    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    @patch("agents.publisher_agent.send_email")
    def test_sends_email_when_env_vars_present(self, mock_send_email, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()
        mock_send_email.return_value = {"messageId": "<123@gmail.com>"}

        env = {"EMAIL_USER": "u@g.com", "EMAIL_PASS": "pw", "EMAIL_TO": "t@g.com"}
        with patch.dict("os.environ", env):
            from agents.publisher_agent import publish_results

            result = publish_results()

        assert result["email"]["status"] == "success"
        assert result["email"]["messageId"] == "<123@gmail.com>"

    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    @patch("agents.publisher_agent.post_to_linkedin")
    def test_posts_linkedin_when_env_vars_present(self, mock_post_li, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()
        mock_post_li.return_value = {"postId": "urn:li:ugcPost:999", "status": 201}

        env = {"LINKEDIN_ACCESS_TOKEN": "tok", "LINKEDIN_PERSON_ID": "pid"}
        with patch.dict("os.environ", env):
            from agents.publisher_agent import publish_results

            result = publish_results()

        # post_to_linkedin returns {"postId": ..., "status": 201}; the 201 overwrites "success"
        assert result["linkedin"]["postId"] == "urn:li:ugcPost:999"
        mock_post_li.assert_called_once()

    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    @patch("agents.publisher_agent.send_email")
    def test_email_failure_recorded_as_error(self, mock_send_email, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()
        mock_send_email.side_effect = Exception("SMTP connection failed")

        env = {"EMAIL_USER": "u@g.com", "EMAIL_PASS": "pw", "EMAIL_TO": "t@g.com"}
        with patch.dict("os.environ", env):
            from agents.publisher_agent import publish_results

            result = publish_results()

        assert result["email"]["status"] == "error"
        assert "SMTP connection failed" in result["email"]["error"]

    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    @patch("agents.publisher_agent.post_to_linkedin")
    def test_linkedin_failure_recorded_as_error(self, mock_post_li, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()
        mock_post_li.side_effect = Exception("401 Unauthorized")

        env = {"LINKEDIN_ACCESS_TOKEN": "bad", "LINKEDIN_PERSON_ID": "pid"}
        with patch.dict("os.environ", env):
            from agents.publisher_agent import publish_results

            result = publish_results()

        assert result["linkedin"]["status"] == "error"
        assert "401" in result["linkedin"]["error"]

    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    def test_always_includes_linkedin_post_preview(self, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()

        import os

        for key in ("EMAIL_USER", "EMAIL_PASS", "EMAIL_TO", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_ID"):
            os.environ.pop(key, None)

        from agents.publisher_agent import publish_results

        result = publish_results()

        assert "linkedin_post_preview" in result
        assert "PulseAI" in result["linkedin_post_preview"]
        assert "#AI" in result["linkedin_post_preview"]

    @patch("agents.publisher_agent.OUTPUT_FILE")
    @patch("agents.publisher_agent.INPUT_FILE")
    def test_writes_output_file(self, mock_input, mock_output, synthesizer_output):
        mock_input.read_text.return_value = json.dumps(synthesizer_output)
        mock_output.write_text = MagicMock()

        import os

        for key in ("EMAIL_USER", "EMAIL_PASS", "EMAIL_TO", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_ID"):
            os.environ.pop(key, None)

        from agents.publisher_agent import publish_results

        publish_results()

        mock_output.write_text.assert_called_once()
        written = mock_output.write_text.call_args[0][0]
        parsed = json.loads(written)
        assert "timestamp" in parsed
        assert "email" in parsed
        assert "linkedin" in parsed
