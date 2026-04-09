# Agent 4: Send the final summary via Email and post to LinkedIn.
# No LLM needed here — pure delivery agent.

import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR.parent / ".env")

INPUT_FILE  = BASE_DIR / "output" / "synthesizer_output.json"
OUTPUT_FILE = BASE_DIR / "output" / "publisher_output.json"

# ── Email via Gmail SMTP ───────────────────────────────────────────────────────

def send_email(subject: str, body: str) -> dict:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = os.environ["EMAIL_USER"]
    msg["To"]      = os.environ["EMAIL_TO"]

    html = f'<pre style="font-family: Arial; font-size: 14px; line-height: 1.6;">{body}</pre>'
    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"])
        server.sendmail(os.environ["EMAIL_USER"], os.environ["EMAIL_TO"], msg.as_string())

    return {"messageId": f"<{datetime.utcnow().timestamp()}@gmail.com>"}

# ── LinkedIn UGC Posts API ─────────────────────────────────────────────────────

def post_to_linkedin(content: str) -> dict:
    post_data = {
        "author": f"urn:li:person:{os.environ['LINKEDIN_PERSON_ID']}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    response = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        json=post_data,
        headers={
            "Authorization":             f"Bearer {os.environ['LINKEDIN_ACCESS_TOKEN']}",
            "Content-Type":              "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        timeout=30,
    )
    response.raise_for_status()
    return {"postId": response.json().get("id"), "status": response.status_code}

# ── LinkedIn post formatter ────────────────────────────────────────────────────

def format_linkedin_post(summary: str) -> str:
    header   = "🤖 Latest AI Update — Powered by PulseAI\n\n"
    hashtags = "\n\n#AI #ArtificialIntelligence #MachineLearning #GenAI #TechTrends"
    return header + summary + hashtags

# ── Main agent function ────────────────────────────────────────────────────────

def publish_results() -> dict:
    print("Agent 4: Publishing results via Email and LinkedIn...")

    input_data   = json.loads(INPUT_FILE.read_text())
    final_summary = input_data["final_summary"]

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "email":     {"status": "skipped"},
        "linkedin":  {"status": "skipped"},
    }

    # ── Send Email ────────────────────────────────────────────────────────────
    if all(os.getenv(k) for k in ("EMAIL_USER", "EMAIL_PASS", "EMAIL_TO")):
        try:
            print("  Sending email...")
            subject = f"PulseAI: Latest AI Update - {datetime.now().strftime('%Y-%m-%d')}"
            body    = f"Latest AI Update\n{'=' * 50}\n\n{final_summary}"
            email_result = send_email(subject, body)
            results["email"] = {"status": "success", **email_result}
            print("  Email sent successfully.")
        except Exception as e:
            results["email"] = {"status": "error", "error": str(e)}
            print(f"  Email failed: {e}")
    else:
        print("  Email skipped: EMAIL_USER, EMAIL_PASS, or EMAIL_TO not set.")

    # ── Post to LinkedIn ──────────────────────────────────────────────────────
    if all(os.getenv(k) for k in ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_ID")):
        try:
            print("  Posting to LinkedIn...")
            post_content = format_linkedin_post(final_summary)
            li_result    = post_to_linkedin(post_content)
            results["linkedin"] = {"status": "success", **li_result}
            print("  LinkedIn post published successfully.")
        except Exception as e:
            results["linkedin"] = {"status": "error", "error": str(e)}
            print(f"  LinkedIn failed: {e}")
    else:
        print("  LinkedIn skipped: LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_ID not set.")

    results["linkedin_post_preview"] = format_linkedin_post(final_summary)

    OUTPUT_FILE.write_text(json.dumps(results, indent=2))
    print("Agent 4: Done! Results published.")
    return results


if __name__ == "__main__":
    publish_results()
