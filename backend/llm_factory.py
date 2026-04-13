# LLM Factory — returns the right CrewAI LLM for each agent.
#
# Resolution order (most specific wins):
#   1. {AGENT_KEY}_MODEL + {AGENT_KEY}_PROVIDER   e.g. PAPER_WRITER_MODEL=claude-opus-4-6
#   2. LLM_MODEL + LLM_PROVIDER                   global override for all agents
#   3. OLLAMA_MODEL + OLLAMA_BASE_URL              local default (always works, no API key)
#
# Supported providers: ollama (default), anthropic, openai
#
# Example .env for research paper quality boost:
#   LLM_PROVIDER=anthropic
#   LLM_MODEL=claude-opus-4-6
#   ANTHROPIC_API_KEY=sk-ant-...
#
# Example per-agent override (only upgrade the paper writer):
#   PAPER_WRITER_PROVIDER=anthropic
#   PAPER_WRITER_MODEL=claude-opus-4-6
#   ANTHROPIC_API_KEY=sk-ant-...

import os
from crewai import LLM

OLLAMA_BASE_URL  = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL     = os.getenv("OLLAMA_MODEL", "llama3.2")


def get_llm(agent_key: str = "", temperature: float | None = None) -> LLM:
    """
    Return a configured CrewAI LLM for the given agent.

    agent_key examples: "ANALYST", "SYNTHESIZER", "PAPER_WRITER",
                        "TREND", "RESEARCH_GAP"
    """
    key = agent_key.upper().replace(" ", "_").replace("-", "_")

    # Agent-specific env vars take priority
    model    = os.getenv(f"{key}_MODEL",    "") or os.getenv("LLM_MODEL",    "")
    provider = os.getenv(f"{key}_PROVIDER", "") or os.getenv("LLM_PROVIDER", "")
    provider = provider.lower()

    kwargs = {} if temperature is None else {"temperature": temperature}

    # Cloud provider requested
    if model and provider and provider != "ollama":
        if provider == "anthropic":
            llm = LLM(
                model=f"anthropic/{model}",
                api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                **kwargs,
            )
        elif provider == "openai":
            llm = LLM(
                model=f"openai/{model}",
                api_key=os.getenv("OPENAI_API_KEY", ""),
                **kwargs,
            )
        else:
            raise ValueError(
                f"Unsupported LLM provider '{provider}'. "
                "Choose 'anthropic', 'openai', or 'ollama'."
            )
        _log(agent_key, provider, model)
        return llm

    # Ollama override (different model but still local)
    if model and (not provider or provider == "ollama"):
        _log(agent_key, "ollama", model)
        return LLM(model=f"ollama/{model}", base_url=OLLAMA_BASE_URL, **kwargs)

    # Default — local Ollama with OLLAMA_MODEL
    _log(agent_key, "ollama", OLLAMA_MODEL)
    return LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL, **kwargs)


def is_cloud_provider(agent_key: str = "") -> bool:
    """Return True if the given agent is configured to use a cloud provider."""
    key      = agent_key.upper().replace(" ", "_").replace("-", "_")
    provider = os.getenv(f"{key}_PROVIDER", "") or os.getenv("LLM_PROVIDER", "")
    return provider.lower() in ("anthropic", "openai")


def _log(agent_key: str, provider: str, model: str) -> None:
    label = f"[{agent_key}] " if agent_key else ""
    print(f"  {label}LLM: {provider}/{model}", flush=True)
