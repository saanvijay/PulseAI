// Agent 2: Organize raw AI news into a structured technical report using Claude

import Anthropic from '@anthropic-ai/sdk';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { config } from 'dotenv';
import { TOKENS } from '../config/tokens.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
config({ path: path.join(__dirname, '../../.env') });

const INPUT_FILE = path.join(__dirname, '../output/researcher_output.json');
const OUTPUT_FILE = path.join(__dirname, '../output/analyst_output.json');

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

async function organizeContent() {
  console.log('Agent 2: Organizing content into a structured report...');

  // Read Agent 1's output
  const rawData = JSON.parse(fs.readFileSync(INPUT_FILE, 'utf-8'));
  const articles = rawData.articles;

  const articlesText = articles
    .map((a) => `Title: ${a.title}\nSnippet: ${a.snippet}\nLink: ${a.link}`)
    .join('\n\n---\n\n');

  const prompt = `You are a senior AI researcher. Based on the following AI news articles, create a comprehensive structured technical report.

ARTICLES:
${articlesText}

Create a detailed report with EXACTLY these 8 sections:

1. **Introduction**
   - Overview of the latest trends found in the articles
   - Why this matters to the AI community

2. **Existing Problems**
   - Key challenges and limitations currently faced in AI
   - Problems that motivated these new developments

3. **Proposed Solutions**
   - New approaches, methods, or models introduced
   - How they address the existing problems

4. **Architecture Overview**
   - A simple ASCII diagram showing how the new AI systems work
   - Key components and their relationships

5. **Advantages**
   - Benefits of the new developments
   - What improvements they bring

6. **Disadvantages**
   - Limitations, risks, or concerns
   - What still needs to be solved

7. **Applied AI Use Cases**
   - Real-world applications of these developments
   - Industries that will benefit

8. **Future Implementation**
   - What to expect next in AI
   - Predictions and upcoming milestones

Keep each section concise but informative. Use bullet points where appropriate.`;

  const message = await client.messages.create({
    model: 'claude-opus-4-6',
    max_tokens: TOKENS.analyst,
    messages: [{ role: 'user', content: prompt }],
  });

  const report = message.content[0].text;

  const output = {
    timestamp: new Date().toISOString(),
    source_articles: articles.length,
    report: report,
  };

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(output, null, 2));
  console.log('Agent 2: Done! Report organized with 8 sections.');
  return output;
}

// Run when called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  organizeContent()
    .then(() => process.exit(0))
    .catch((err) => {
      console.error('Agent 2 Error:', err.message);
      process.exit(1);
    });
}

export { organizeContent };
