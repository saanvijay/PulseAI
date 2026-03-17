// Agent 1: Fetch the latest AI concepts using Claude's built-in web search tool.
// Sources: ArXiv, Papers with Code, Hugging Face, lab blogs (Anthropic, OpenAI, DeepMind,
//          Meta AI, Mistral), newsletters (The Batch, Import AI), news (VentureBeat,
//          TechCrunch, Wired), community (Reddit, LinkedIn, X/Twitter).

import Anthropic from '@anthropic-ai/sdk';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { config } from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
config({ path: path.join(__dirname, '../.env') });

const OUTPUT_FILE = path.join(__dirname, '../output/agent1_output.json');

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// All sources to search, grouped by category
const SOURCES = {
  research: [
    { query: 'site:arxiv.org/abs AI machine learning 2026',         label: 'ArXiv' },
    { query: 'site:paperswithcode.com latest AI state of the art',  label: 'Papers with Code' },
  ],
  lab_blogs: [
    { query: 'site:anthropic.com/research latest 2026',             label: 'Anthropic Research' },
    { query: 'site:openai.com/blog latest 2026',                    label: 'OpenAI Blog' },
    { query: 'site:deepmind.google/research latest 2026',           label: 'Google DeepMind' },
    { query: 'site:ai.meta.com/blog latest 2026',                   label: 'Meta AI Blog' },
    { query: 'site:mistral.ai/news 2026',                           label: 'Mistral' },
    { query: 'site:huggingface.co/blog 2026',                       label: 'Hugging Face Blog' },
  ],
  newsletters: [
    { query: 'site:deeplearning.ai/the-batch 2026',                 label: 'The Batch' },
    { query: '"Import AI" Jack Clark newsletter 2026',              label: 'Import AI' },
  ],
  news: [
    { query: 'site:venturebeat.com AI 2026',                        label: 'VentureBeat' },
    { query: 'site:techcrunch.com artificial-intelligence 2026',    label: 'TechCrunch AI' },
    { query: 'site:wired.com artificial-intelligence 2026',         label: 'Wired AI' },
  ],
  community: [
    { query: 'site:reddit.com/r/MachineLearning top posts 2026',   label: 'Reddit r/MachineLearning' },
    { query: 'site:reddit.com/r/LocalLLaMA top posts 2026',        label: 'Reddit r/LocalLLaMA' },
    { query: 'site:linkedin.com/pulse AI artificial intelligence 2026', label: 'LinkedIn' },
    { query: 'AI breakthroughs twitter x.com 2026',                label: 'X/Twitter' },
  ],
};

// Flat list of all searches with their category tag
const ALL_SEARCHES = Object.entries(SOURCES).flatMap(([category, items]) =>
  items.map((s) => ({ ...s, category }))
);

// Claude will use this prompt to autonomously search all sources
const SEARCH_PROMPT = `You are an AI research assistant. Use the web search tool to find the latest AI developments.

Run a separate web search for EACH of the following ${ALL_SEARCHES.length} queries (search them all):

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

async function fetchLatestAIConcepts() {
  const sourceNames = ALL_SEARCHES.map((s) => s.label).join(', ');
  console.log(`Agent 1: Searching ${ALL_SEARCHES.length} sources — ${sourceNames}`);

  const messages = [{ role: 'user', content: SEARCH_PROMPT }];
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
    total: articles.length,
    sources_searched: ALL_SEARCHES.map((s) => s.label),
    articles,
  };

  fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(output, null, 2));
  console.log(`Agent 1: Done! Found ${articles.length} results across ${ALL_SEARCHES.length} sources.`);
  return output;
}

// Run when called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  fetchLatestAIConcepts()
    .then(() => process.exit(0))
    .catch((err) => {
      console.error('Agent 1 Error:', err.message);
      process.exit(1);
    });
}

export { fetchLatestAIConcepts };
