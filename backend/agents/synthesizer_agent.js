// Agent 3: Send the report to 5 AI models and create a final consolidated summary.
// GPT-4o, Gemini, Mistral, and Cohere are all routed through OpenRouter (one API key).
// Claude is called directly via the Anthropic SDK.

import Anthropic from '@anthropic-ai/sdk';
import OpenAI from 'openai';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { config } from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
config({ path: path.join(__dirname, '../../.env') });

const INPUT_FILE = path.join(__dirname, '../output/analyst_output.json');
const OUTPUT_FILE = path.join(__dirname, '../output/synthesizer_output.json');

// Claude — direct Anthropic SDK
const claude = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// All other models — single OpenRouter client (OpenAI-compatible)
const openrouter = new OpenAI({
  apiKey: process.env.OPENROUTER_API_KEY,
  baseURL: 'https://openrouter.ai/api/v1',
  defaultHeaders: { 'X-Title': 'PulseAI' },
});

// Helper: call any model through OpenRouter
async function askViaOpenRouter(model, report) {
  const response = await openrouter.chat.completions.create({
    model,
    max_tokens: 1000,
    messages: [
      {
        role: 'user',
        content: `Summarize this AI report in 3-4 key insights:\n\n${report}`,
      },
    ],
  });
  return response.choices[0].message.content;
}

// --- Individual model functions ---

async function askClaude(report) {
  const response = await claude.messages.create({
    model: 'claude-opus-4-6',
    max_tokens: 1000,
    messages: [
      {
        role: 'user',
        content: `Summarize this AI report in 3-4 key insights:\n\n${report}`,
      },
    ],
  });
  return response.content[0].text;
}

async function askGPT4(report)    { return askViaOpenRouter('openai/gpt-4o', report); }
async function askGemini(report)  { return askViaOpenRouter('google/gemini-pro-1.5', report); }
async function askMistral(report) { return askViaOpenRouter('mistralai/mistral-large', report); }
async function askCohere(report)  { return askViaOpenRouter('cohere/command-r-plus', report); }

// --- Helper to safely call each model ---
async function callModel(name, fn, report) {
  try {
    console.log(`  Asking ${name}...`);
    const result = await fn(report);
    return { model: name, status: 'success', summary: result };
  } catch (err) {
    console.log(`  ${name} failed: ${err.message}`);
    return { model: name, status: 'error', error: err.message, summary: null };
  }
}

// --- Create a final summary from all model responses ---
async function createFinalSummary(report, modelResponses) {
  const successfulResponses = modelResponses.filter((r) => r.status === 'success');

  const responsesText = successfulResponses
    .map((r) => `[${r.model}]:\n${r.summary}`)
    .join('\n\n---\n\n');

  const prompt = `You received summaries of an AI report from ${successfulResponses.length} different AI models.
Your job is to create ONE final consolidated summary that captures the best insights from all models.

ORIGINAL REPORT:
${report}

MODEL SUMMARIES:
${responsesText}

Write a final summary that:
1. Combines the best points from all models
2. Highlights the most important AI developments
3. Is clear and easy to understand
4. Is suitable for a LinkedIn post (professional tone)
5. Is between 200-300 words`;

  const response = await claude.messages.create({
    model: 'claude-opus-4-6',
    max_tokens: 1000,
    messages: [{ role: 'user', content: prompt }],
  });

  return response.content[0].text;
}

async function summarizeWithMultipleModels() {
  console.log('Agent 3: Getting summaries from 5 AI models...');

  const inputData = JSON.parse(fs.readFileSync(INPUT_FILE, 'utf-8'));
  const report = inputData.report;

  // Call all 5 models in parallel
  const [claudeResult, gpt4Result, geminiResult, mistralResult, cohereResult] =
    await Promise.all([
      callModel('Claude Opus 4.6', askClaude, report),
      callModel('GPT-4o', askGPT4, report),
      callModel('Gemini 1.5 Pro', askGemini, report),
      callModel('Mistral Large', askMistral, report),
      callModel('Cohere Command R+', askCohere, report),
    ]);

  const modelResponses = [
    claudeResult,
    gpt4Result,
    geminiResult,
    mistralResult,
    cohereResult,
  ];

  const successCount = modelResponses.filter((r) => r.status === 'success').length;
  console.log(`  ${successCount}/5 models responded successfully.`);

  console.log('  Creating final consolidated summary...');
  const finalSummary = await createFinalSummary(report, modelResponses);

  const output = {
    timestamp: new Date().toISOString(),
    models_queried: 5,
    models_successful: successCount,
    model_responses: modelResponses,
    final_summary: finalSummary,
  };

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(output, null, 2));
  console.log('Agent 3: Done! Final summary created from all model responses.');
  return output;
}

// Run when called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  summarizeWithMultipleModels()
    .then(() => process.exit(0))
    .catch((err) => {
      console.error('Agent 3 Error:', err.message);
      process.exit(1);
    });
}

export { summarizeWithMultipleModels };
