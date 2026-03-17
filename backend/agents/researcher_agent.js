// Agent 1: Fetch the latest AI concepts using Claude's built-in web search tool.
// Sources: ArXiv, Papers with Code, Hugging Face, lab blogs (Anthropic, OpenAI, DeepMind,
//          Meta AI, Mistral), newsletters (The Batch, Import AI), news (VentureBeat,
//          TechCrunch, Wired), community (Reddit, LinkedIn, X/Twitter).

import Anthropic from '@anthropic-ai/sdk';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { config } from 'dotenv';
import { SOURCES } from '../config/sources.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
config({ path: path.join(__dirname, '../../.env') });

const OUTPUT_FILE = path.join(__dirname, '../output/researcher_output.json');

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// Flat list of all active (uncommented) sources with their category tag
const ALL_SEARCHES = Object.entries(SOURCES).flatMap(([category, items]) =>
  items.map((s) => ({ ...s, category }))
);

function buildSearchPrompt(topic) {
  const topicLine = topic
    ? `Focus specifically on: "${topic}"\n\n`
    : '';

  return `You are an AI research assistant. Use the web search tool to find the latest AI developments.

${topicLine}Run a separate web search for EACH of the following ${ALL_SEARCHES.length} queries (search them all):

${ALL_SEARCHES.map((s, i) => `${i + 1}. "${s.query}" — ${s.label}`).join('\n')}

After completing all searches, compile every result into a single JSON array. Return ONLY the raw JSON array with no explanation or markdown:

[
  {
    "title": "title of the article, paper, or post",
    "snippet": "2-3 sentence summary of the content",
    "link": "full URL",
    "source": "source name (e.g. ArXiv, OpenAI Blog, VentureBeat...)",
    "category": "research | lab_blogs | newsletters | news | community",
    "date": "publication date if visible, otherwise null"
  }
]

Aim for at least 2-3 results per source. Total should be 25-30 results.`;
}

async function fetchLatestAIConcepts(topic = '') {
  const sourceNames = ALL_SEARCHES.map((s) => s.label).join(', ');
  console.log(`Agent 1: Searching ${ALL_SEARCHES.length} sources — ${sourceNames}`);
  if (topic) console.log(`  Topic: "${topic}"`);

  const messages = [{ role: 'user', content: buildSearchPrompt(topic) }];
  let finalText = '';

  // Loop handles pause_turn — triggered when Claude's server-side search
  // loop reaches its default 10-iteration limit and needs to continue
  for (let iteration = 0; iteration < 5; iteration++) {
    const response = await client.messages.create({
      model: 'claude-opus-4-6',
      max_tokens: 8000,
      tools: [
        { type: 'web_search_20260209', name: 'web_search' },
      ],
      messages,
    });

    // Log which sources Claude is searching
    for (const block of response.content) {
      if (block.type === 'server_tool_use' && block.name === 'web_search') {
        console.log(`  Searching: "${block.input.query}"`);
      }
    }

    // Append the full response (including tool use blocks) for continuation
    messages.push({ role: 'assistant', content: response.content });

    if (response.stop_reason === 'end_turn') {
      const textBlock = response.content.find((b) => b.type === 'text');
      if (textBlock) finalText = textBlock.text;
      break;
    }

    // pause_turn means the server-side search loop hit its limit — keep going
    if (response.stop_reason !== 'pause_turn') break;
  }

  // Extract the JSON array from Claude's response
  let articles = [];
  try {
    const jsonMatch = finalText.match(/\[[\s\S]*\]/);
    if (jsonMatch) {
      articles = JSON.parse(jsonMatch[0]);
    } else {
      throw new Error('No JSON array found in response');
    }
  } catch (err) {
    console.warn(`  Could not parse JSON (${err.message}), saving raw response.`);
    articles = [{
      title: 'Raw Claude response',
      snippet: finalText.slice(0, 500),
      link: '',
      source_type: 'web',
      date: null,
    }];
  }

  const output = {
    timestamp: new Date().toISOString(),
    topic: topic || 'Latest AI updates',
    total: articles.length,
    sources_searched: ALL_SEARCHES.map((s) => s.label),
    articles,
  };

  fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(output, null, 2));
  console.log(`Agent 1: Done! Found ${articles.length} results across ${ALL_SEARCHES.length} sources.`);
  return output;
}

// Run when called directly: node researcher_agent.js "optional topic"
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const topic = process.argv[2] || '';
  fetchLatestAIConcepts(topic)
    .then(() => process.exit(0))
    .catch((err) => {
      console.error('Agent 1 Error:', err.message);
      process.exit(1);
    });
}

export { fetchLatestAIConcepts };
