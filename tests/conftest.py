"""
conftest.py — Shared Pytest Fixtures for Agent Test Suite
"""

import pytest
from agent.ollama_client import OllamaClient


@pytest.fixture(scope="session")
def ollama_check():
    """Session-wide fixture to verify Ollama reachability, model availability, and generation responsiveness."""
    client = OllamaClient()
    if not client.is_reachable() or not client.is_model_available():
        pytest.skip("Ollama service or target model is not available locally")

    # Verify that model generation actually responds cleanly without timing out or raising errors
    try:
        ping_res = client.generate_response("Reply with 'OK'")
        if not ping_res or len(ping_res.strip()) == 0:
            pytest.skip("Ollama service is reachable but model returned empty response")
    except Exception as e:
        pytest.skip(f"Ollama service is reachable but model generation failed: {e}")
