// Agent 4: Send the final summary via Email and post to LinkedIn

import nodemailer from 'nodemailer';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { config } from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
config({ path: path.join(__dirname, '../../.env') });

const INPUT_FILE = path.join(__dirname, '../output/synthesizer_output.json');
const OUTPUT_FILE = path.join(__dirname, '../output/publisher_output.json');

// --- Send Email via Gmail ---
async function sendEmail(subject, body) {
  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS, // Use Gmail App Password (not your real password)
    },
  });

  const mailOptions = {
    from: process.env.EMAIL_USER,
    to: process.env.EMAIL_TO,
    subject: subject,
    text: body,
    html: `<pre style="font-family: Arial; font-size: 14px; line-height: 1.6;">${body}</pre>`,
  };

  const result = await transporter.sendMail(mailOptions);
  return { messageId: result.messageId, accepted: result.accepted };
}

// --- Post to LinkedIn ---
// Requires: LinkedIn Developer App with r_liteprofile + w_member_social permissions
// Get access token from: https://www.linkedin.com/developers/tools/oauth
async function postToLinkedIn(content) {
  const postData = {
    author: `urn:li:person:${process.env.LINKEDIN_PERSON_ID}`,
    lifecycleState: 'PUBLISHED',
    specificContent: {
      'com.linkedin.ugc.ShareContent': {
        shareCommentary: {
          text: content,
        },
        shareMediaCategory: 'NONE',
      },
    },
    visibility: {
      'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC',
    },
  };

  const response = await axios.post(
    'https://api.linkedin.com/v2/ugcPosts',
    postData,
    {
      headers: {
        Authorization: `Bearer ${process.env.LINKEDIN_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
      },
    }
  );

  return { postId: response.data.id, status: response.status };
}

// --- Format LinkedIn post from the final summary ---
function formatLinkedInPost(summary) {
  const hashtags = '\n\n#AI #ArtificialIntelligence #MachineLearning #GenAI #TechTrends';
  const header = '🤖 Latest AI Update — Powered by PulseAI\n\n';
  return header + summary + hashtags;
}

async function publishResults() {
  console.log('Agent 4: Publishing results via Email and LinkedIn...');

  const inputData = JSON.parse(fs.readFileSync(INPUT_FILE, 'utf-8'));
  const finalSummary = inputData.final_summary;

  const results = {
    timestamp: new Date().toISOString(),
    email: { status: 'skipped' },
    linkedin: { status: 'skipped' },
  };

  // --- Send Email ---
  if (process.env.EMAIL_USER && process.env.EMAIL_PASS && process.env.EMAIL_TO) {
    try {
      console.log('  Sending email...');
      const emailSubject = `PulseAI: Latest AI Update - ${new Date().toLocaleDateString()}`;
      const emailBody = `Latest AI Update\n${'='.repeat(50)}\n\n${finalSummary}`;
      const emailResult = await sendEmail(emailSubject, emailBody);
      results.email = { status: 'success', ...emailResult };
      console.log('  Email sent successfully.');
    } catch (err) {
      results.email = { status: 'error', error: err.message };
      console.log(`  Email failed: ${err.message}`);
    }
  } else {
    console.log('  Email skipped: EMAIL_USER, EMAIL_PASS, or EMAIL_TO not set.');
  }

  // --- Post to LinkedIn ---
  if (process.env.LINKEDIN_ACCESS_TOKEN && process.env.LINKEDIN_PERSON_ID) {
    try {
      console.log('  Posting to LinkedIn...');
      const linkedInPost = formatLinkedInPost(finalSummary);
      const linkedInResult = await postToLinkedIn(linkedInPost);
      results.linkedin = { status: 'success', ...linkedInResult };
      console.log('  LinkedIn post published successfully.');
    } catch (err) {
      results.linkedin = { status: 'error', error: err.message };
      console.log(`  LinkedIn failed: ${err.message}`);
    }
  } else {
    console.log('  LinkedIn skipped: LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_ID not set.');
  }

  results.linkedin_post_preview = formatLinkedInPost(finalSummary);

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(results, null, 2));
  console.log('Agent 4: Done! Results published.');
  return results;
}

// Run when called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  publishResults()
    .then(() => process.exit(0))
    .catch((err) => {
      console.error('Agent 4 Error:', err.message);
      process.exit(1);
    });
}

export { publishResults };
