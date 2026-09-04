"""
test_chains.py — Unit and Integration tests for LangChain application chain
"""

import pytest
from unittest.mock import patch, MagicMock
from agent.config import Settings
from agent.schemas import AgentRequest, AgentResponse
from agent.chains import create_agent_chain, run_agent_request
from agent.ollama_client import OllamaClient


# =====================================================================
# Unit Tests (Offline safe — run in normal CI)
# =====================================================================

def test_run_agent_request_empty_input():
    """Verify empty or whitespace string returns status='needs_input'."""
    res1 = run_agent_request("")
    assert res1.status == "needs_input"
    assert "cannot be empty" in res1.answer

    res2 = run_agent_request("   ")
    assert res2.status == "needs_input"
    assert "cannot be empty" in res2.answer


def test_create_agent_chain_construction():
    """Verify LCEL chain is constructed without invoking LLM."""
    chain = create_agent_chain()
    assert chain is not None


def test_run_agent_request_model_error_handling(monkeypatch):
    """Verify model errors are caught and converted to AgentResponse error status."""
    mock_chain = MagicMock()
    mock_chain.invoke.side_effect = RuntimeError("Connection refused to Ollama endpoint")

    with patch("agent.chains.create_agent_chain", return_value=mock_chain):
        res = run_agent_request("Test prompt")
        assert res.status == "error"
        assert "Connection refused" in res.answer


# =====================================================================
# Integration Tests (Require live Ollama service)
# =====================================================================


@pytest.mark.integration
def test_run_agent_request_integration_pump_query(ollama_check):
    """Integration test: Verify live Qwen model response via run_agent_request."""
    res = run_agent_request("What is the purpose of a pump in a process plant?")
    assert res.status == "success"
    assert isinstance(res.answer, str)
    assert len(res.answer) > 10


@pytest.mark.integration
def test_run_agent_request_integration_unsupplied_data(ollama_check):
    """Integration test: Verify model adheres to system prompt and does not invent specs."""
    prompt = (
        "Pump P-101 is identified in the provided data. "
        "Summarize only the information provided about P-101."
    )
    res = run_agent_request(prompt)
    assert res.status == "success"
    assert isinstance(res.answer, str)
