"""
llm.py — ChatOllama LLM Instance Builder for Member 2 Agent
"""

from typing import Optional
from langchain_ollama import ChatOllama
from .config import Settings, settings


def get_llm(config: Optional[Settings] = None) -> ChatOllama:
    """Returns a ChatOllama instance configured from Settings."""
    cfg = config or settings
    return ChatOllama(
        model=cfg.ollama_model,
        base_url=cfg.ollama_base_url,
        temperature=cfg.temperature,
        timeout=cfg.request_timeout,
    )
