"""
test_config.py — Unit tests for agent configuration (runs offline)
"""

import os
from agent.config import Settings


def test_default_settings():
    """Verify default setting values when environment variables are unset."""
    s = Settings()
    assert s.ollama_base_url == "http://localhost:11434"
    assert s.ollama_model == "qwen2.5-coder:1.5b"
    assert s.temperature == 0.0


def test_custom_env_settings(monkeypatch):
    """Verify custom environment variables override defaults properly."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/")
    monkeypatch.setenv("OLLAMA_MODEL", "custom-model")
    monkeypatch.setenv("TEMPERATURE", "0.5")

    s = Settings()
    assert s.ollama_base_url == "http://127.0.0.1:11434"
    assert s.ollama_model == "custom-model"
    assert s.temperature == 0.5
