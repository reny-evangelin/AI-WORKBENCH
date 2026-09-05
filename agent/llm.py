"""
llm.py — ChatOllama LLM Instance Builder for Member 2 Agent
"""

from typing import Optional
from langchain_ollama import ChatOllama
from .config import Settings, settings


_llm_instance = None

def get_llm(config: Optional[Settings] = None):
    """
    Initializes and returns a globally cached ChatOllama LLM instance.
    If a custom config is provided, returns a new instance without caching.
    """
    global _llm_instance
    
    # If custom config is provided, don't use cache
    if config is not None:
        return ChatOllama(
            model=config.ollama_model,
            base_url=config.ollama_base_url,
            temperature=config.temperature,
            format="json", 
        )

    if _llm_instance is None:
        cfg = settings
        _llm_instance = ChatOllama(
            model=cfg.ollama_model,
            base_url=cfg.ollama_base_url,
            temperature=cfg.temperature,
            format="json", 
        )
    return _llm_instance
