"""
test_graph.py — Unit and Integration tests for LangGraph Agent Workflow
"""

import pytest
from unittest.mock import patch
from agent.schemas import AgentResponse
from agent.graph.router import route_request_intent
from agent.graph.workflow import build_agent_graph, run_agent
from agent.ollama_client import OllamaClient


# =====================================================================
# Unit Tests (Offline safe — run in normal CI)
# =====================================================================

def test_graph_compilation():
    """Verify that the LangGraph workflow compiles successfully."""
    graph = build_agent_graph()
    assert graph is not None


def test_empty_input_routing():
    """Test 1: Empty input returns needs_input status without calling LLM."""
    with patch("agent.graph.nodes.run_agent_request") as mock_chain:
        res = run_agent("")
        assert res.status == "needs_input"
        assert "cannot be empty" in res.answer
        mock_chain.assert_not_called()


def test_deterministic_router():
    """Verify deterministic router intent mapping."""
    assert route_request_intent("What is a centrifugal pump?") == "general"
    assert route_request_intent("Explain this P&ID diagram") == "pid"
    assert route_request_intent("What does API 610 say about pumps?") == "knowledge"
    assert route_request_intent("Create an Excel report") == "document"
    assert route_request_intent("q") == "unknown"


def test_general_routing_offline():
    """Test 2: General query routing to general_response node."""
    assert route_request_intent("What is a pump?") == "general"

    mock_response = AgentResponse(
        answer="A pump is a mechanical device used to move fluids.",
        status="success",
        sources=[],
    )
    with patch("agent.graph.nodes.run_agent_request", return_value=mock_response):
        res = run_agent("What is a pump?")
        assert res.status == "success"
        assert "mechanical device" in res.answer


def test_pid_routing():
    """Test 3: P&ID request routes to analyze_pid tool action and requests missing file input."""
    res = run_agent("Explain this P&ID")
    assert res.status == "needs_input"
    assert "P&ID file path" in res.answer


def test_knowledge_routing():
    """Test 4: Knowledge request routes to search_knowledge tool action."""
    res = run_agent("What does API 610 say about pumps?")
    assert res.status == "success"
    assert "search_knowledge" in res.answer


def test_document_routing():
    """Test 5: Document request routes to generate_excel tool action."""
    res = run_agent("Create an Excel report")
    assert res.status == "success"
    assert "File:" in res.answer or "generate_excel" in res.answer


def test_unknown_routing():
    """Test 6: Ambiguous/unrecognized single-token request routes to general response node."""
    mock_response = AgentResponse(
        answer="Unable to determine request category. Please clarify.",
        status="needs_input",
        sources=[],
    )
    with patch("agent.graph.nodes.run_agent_request", return_value=mock_response):
        res = run_agent("x")
        assert res.status == "needs_input"
        assert "clarify" in res.answer


# =====================================================================
# Integration Tests (Require live Ollama service)
# =====================================================================


@pytest.mark.integration
def test_run_agent_integration_general_query(ollama_check):
    """Integration test: Verify live end-to-end execution of run_agent via LangGraph."""
    res = run_agent("What is the purpose of a pump in a process plant?")
    assert res.status in ("success", "error")
    assert isinstance(res.answer, str)
    assert len(res.answer) > 10
