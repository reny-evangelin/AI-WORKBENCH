"""
llm.py — Ollama LLM Connection & Configuration
Member 2: Main AI Agent

Responsibilities:
- Connect to local Ollama instance
- Configure the LLM (model, temperature, timeout)
- Expose a reusable LLM instance for the rest of the agent
"""

from langchain_ollama import ChatOllama

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

OLLAMA_BASE_URL = "http://localhost:11434"   # Default Ollama local server
OLLAMA_MODEL    = "qwen2.5-coder:1.5b"      # Lightweight model for development
TEMPERATURE     = 0.0                        # Deterministic output for engineering tasks
REQUEST_TIMEOUT = 120                        # Seconds before timeout


# ─────────────────────────────────────────────
# LLM Instance
# ─────────────────────────────────────────────

def get_llm(
    model: str = OLLAMA_MODEL,
    temperature: float = TEMPERATURE,
    base_url: str = OLLAMA_BASE_URL,
    timeout: int = REQUEST_TIMEOUT,
) -> ChatOllama:
    """
    Returns a configured ChatOllama instance.

    Args:
        model:       Ollama model name (default: qwen2.5-coder:1.5b)
        temperature: Sampling temperature. 0.0 = deterministic.
        base_url:    Ollama server URL.
        timeout:     Request timeout in seconds.

    Returns:
        ChatOllama: Ready-to-use LLM instance.
    """
    return ChatOllama(
        model=model,
        temperature=temperature,
        base_url=base_url,
        timeout=timeout,
    )


# Default shared LLM instance used across the agent
llm = get_llm()
