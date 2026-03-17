// ─────────────────────────────────────────────────────────────────────────────
// PulseAI — Source Configuration
//
// Uncomment any source to include it in the next research run.
// Each active source costs one Claude web-search call.
// Default: 3 sources for a quick test run.
// ─────────────────────────────────────────────────────────────────────────────

export const SOURCES = {

  research: [
    // { query: 'site:arxiv.org/abs AI machine learning 2026',        label: 'ArXiv' },
    // { query: 'site:paperswithcode.com latest AI state of the art', label: 'Papers with Code' },
  ],

  lab_blogs: [
    { query: 'site:anthropic.com/research latest 2026',              label: 'Anthropic Research' },
    { query: 'site:openai.com/blog latest 2026',                     label: 'OpenAI Blog' },
    { query: 'site:deepmind.google/research latest 2026',            label: 'Google DeepMind' },
    // { query: 'site:ai.meta.com/blog latest 2026',                  label: 'Meta AI Blog' },
    // { query: 'site:mistral.ai/news 2026',                          label: 'Mistral' },
    // { query: 'site:huggingface.co/blog 2026',                      label: 'Hugging Face Blog' },
  ],

  newsletters: [
    // { query: 'site:deeplearning.ai/the-batch 2026',                label: 'The Batch' },
    // { query: '"Import AI" Jack Clark newsletter 2026',             label: 'Import AI' },
  ],

  news: [
    // { query: 'site:venturebeat.com AI 2026',                       label: 'VentureBeat' },
    // { query: 'site:techcrunch.com artificial-intelligence 2026',   label: 'TechCrunch AI' },
    // { query: 'site:wired.com artificial-intelligence 2026',        label: 'Wired AI' },
  ],

  community: [
    // { query: 'site:reddit.com/r/MachineLearning top posts 2026',  label: 'Reddit r/MachineLearning' },
    // { query: 'site:reddit.com/r/LocalLLaMA top posts 2026',       label: 'Reddit r/LocalLLaMA' },
    // { query: 'site:linkedin.com/pulse AI artificial intelligence 2026', label: 'LinkedIn' },
    // { query: 'AI breakthroughs twitter x.com 2026',               label: 'X/Twitter' },
  ],

};
