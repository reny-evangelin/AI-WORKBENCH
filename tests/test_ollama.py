"""
test_ollama.py — Integration tests for Ollama connection layer
"""

import pytest
from agent.config import Settings
from agent.ollama_client import OllamaClient


@pytest.fixture
def client():
    return OllamaClient(Settings())


def test_ollama_client_init(client):
    """Unit test for client initialization (offline safe)."""
    assert client.config.ollama_model == "qwen2.5-coder:1.5b"
    assert client.config.ollama_base_url == "http://localhost:11434"


@pytest.mark.integration
def test_ollama_reachability(client):
    """Integration test: Check if Ollama server is reachable."""
    if not client.is_reachable():
        pytest.skip("Ollama service not available locally")
    assert client.is_reachable() is True


@pytest.mark.integration
def test_ollama_model_availability(client):
    """Integration test: Check if target model exists."""
    if not client.is_reachable():
        pytest.skip("Ollama service not available locally")
    assert client.is_model_available() is True
