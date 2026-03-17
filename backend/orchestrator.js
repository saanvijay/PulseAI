// Orchestrator: Runs all agents in sequence

import { fetchLatestAIConcepts } from './agents/researcher_agent.js';
import { organizeContent }       from './agents/analyst_agent.js';
import { summarizeWithMultipleModels } from './agents/synthesizer_agent.js';
import { publishResults }        from './agents/publisher_agent.js';

async function runPipeline() {
  console.log('\n========================================');
  console.log('  PulseAI - Multi-Agent Pipeline');
  console.log('========================================\n');

  const startTime = Date.now();

  // Researcher: Fetch AI news from 16 sources
  console.log('\n[Step 1/4] Researcher Agent: Fetching AI News');
  const t1 = Date.now();
  await fetchLatestAIConcepts();
  console.log(`  Completed in ${((Date.now() - t1) / 1000).toFixed(1)}s\n`);

  // Analyst: Organize into structured report
  console.log('[Step 2/4] Analyst Agent: Organizing Content');
  const t2 = Date.now();
  await organizeContent();
  console.log(`  Completed in ${((Date.now() - t2) / 1000).toFixed(1)}s\n`);

  // Synthesizer: Multi-model summary
  console.log('[Step 3/4] Synthesizer Agent: Multi-Model Summary');
  const t3 = Date.now();
  await summarizeWithMultipleModels();
  console.log(`  Completed in ${((Date.now() - t3) / 1000).toFixed(1)}s\n`);

  // Publisher: Email + LinkedIn
  console.log('[Step 4/4] Publisher Agent: Publishing Results');
  const t4 = Date.now();
  await publishResults();
  console.log(`  Completed in ${((Date.now() - t4) / 1000).toFixed(1)}s\n`);

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
