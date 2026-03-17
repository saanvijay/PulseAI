// Trend Agent: Scans the active sources from config/sources.js and identifies
// the single most trending AI topic right now. Used to auto-fill the topic box
// in the Streamlit dashboard when the user hasn't provided their own topic.

import Anthropic from '@anthropic-ai/sdk';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { config } from 'dotenv';
import { SOURCES } from '../config/sources.js';
import { TOKENS } from '../config/tokens.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
config({ path: path.join(__dirname, '../../.env') });

const OUTPUT_FILE = path.join(__dirname, '../output/trend_output.json');

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// Only use active (uncommented) sources from the config
const ALL_SEARCHES = Object.entries(SOURCES).flatMap(([category, items]) =>
  items.map((s) => ({ ...s, category }))
);

async function getTrendingTopic() {
  console.log(`Trend Agent: Scanning ${ALL_SEARCHES.length} active sources for trending topics...`);

  const sourceList = ALL_SEARCHES.map((s) => s.label).join(', ');

  const prompt = `You are an AI trend analyst. Use web search to quickly scan the latest news from these AI sources: ${sourceList}.

Do a few targeted searches to find what the AI industry is talking about most right now.

Then respond with ONLY a short topic phrase (3–6 words) — the single most trending AI topic at this moment.
No explanation, no bullet points, no punctuation. Just the phrase.

Good examples:
- LLM reasoning and planning
- Multimodal foundation models
- AI agents and autonomy
- Retrieval-augmented generation`;

  const messages = [{ role: 'user', content: prompt }];
  let topic = '';

  for (let i = 0; i < 3; i++) {
    const response = await client.messages.create({
      model: 'claude-opus-4-6',
      max_tokens: TOKENS.trend,
      tools: [{ type: 'web_search_20260209', name: 'web_search' }],
      messages,
    });

    for (const block of response.content) {
      if (block.type === 'server_tool_use' && block.name === 'web_search') {
        console.log(`  Searching: "${block.input.query}"`);
      }
    }

    messages.push({ role: 'assistant', content: response.content });

    if (response.stop_reason === 'end_turn') {
      const textBlock = response.content.find((b) => b.type === 'text');
      if (textBlock) topic = textBlock.text.trim();
      break;
    }
    if (response.stop_reason !== 'pause_turn') break;
  }

  const output = {
    timestamp: new Date().toISOString(),
    topic,
    sources_scanned: ALL_SEARCHES.map((s) => s.label),
  };

  fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(output, null, 2));
  console.log(`Trend Agent: Trending topic → "${topic}"`);
  return output;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  getTrendingTopic()
    .then(() => process.exit(0))
    .catch((err) => {
      console.error('Trend Agent Error:', err.message);
      process.exit(1);
    });
}

export { getTrendingTopic };
