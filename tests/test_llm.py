"""
test_llm.py — Offline unit tests for ChatOllama LLM factory
"""

from agent.config import Settings
from agent.llm import get_llm


def test_get_llm_defaults():
    """Verify get_llm creates ChatOllama with default configuration."""
    llm = get_llm()
    assert llm.model == "qwen2.5-coder:1.5b"
    assert llm.base_url == "http://localhost:11434"
    assert llm.temperature == 0.0


def test_get_llm_custom_config():
    """Verify get_llm creates ChatOllama with custom Settings instance."""
    import agent.llm
    agent.llm._llm_instance = None
    
    cfg = Settings()
    cfg.ollama_model = "custom-model"
    cfg.ollama_base_url = "http://127.0.0.1:11434"
    cfg.temperature = 0.7

    llm = get_llm(cfg)
    assert llm.model == "custom-model"
    assert llm.base_url == "http://127.0.0.1:11434"
    assert llm.temperature == 0.7
    
    agent.llm._llm_instance = None
