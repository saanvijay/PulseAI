// Orchestrator: Runs all 4 agents in sequence

import { fetchLatestAIConcepts } from './agents/agent1_fetch.js';
import { organizeContent } from './agents/agent2_organize.js';
import { summarizeWithMultipleModels } from './agents/agent3_summarize.js';
import { publishResults } from './agents/agent4_publish.js';

async function runPipeline() {
  console.log('\n========================================');
  console.log('  PulseAI - Multi-Agent Pipeline');
  console.log('========================================\n');

  const startTime = Date.now();

  // Agent 1: Fetch AI news
  console.log('\n[Step 1/4] Running Agent 1: Fetch AI News');
  const agent1Start = Date.now();
  await fetchLatestAIConcepts();
  console.log(`  Completed in ${((Date.now() - agent1Start) / 1000).toFixed(1)}s\n`);

  // Agent 2: Organize content
  console.log('[Step 2/4] Running Agent 2: Organize Content');
  const agent2Start = Date.now();
  await organizeContent();
  console.log(`  Completed in ${((Date.now() - agent2Start) / 1000).toFixed(1)}s\n`);

  // Agent 3: Multi-model summary
  console.log('[Step 3/4] Running Agent 3: Multi-Model Summary');
  const agent3Start = Date.now();
  await summarizeWithMultipleModels();
  console.log(`  Completed in ${((Date.now() - agent3Start) / 1000).toFixed(1)}s\n`);

  // Agent 4: Publish
  console.log('[Step 4/4] Running Agent 4: Publish Results');
  const agent4Start = Date.now();
  await publishResults();
  console.log(`  Completed in ${((Date.now() - agent4Start) / 1000).toFixed(1)}s\n`);

  const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log('========================================');
  console.log(`  Pipeline Complete! Total time: ${totalTime}s`);
  console.log('  Outputs saved to the output/ folder');
  console.log('========================================\n');
}

runPipeline().catch((err) => {
  console.error('\nPipeline failed:', err.message);
  process.exit(1);
});
