"""
test_conversation.py — Unit and Integration tests for conversational agent flow
"""

import pytest
from unittest.mock import patch, MagicMock
from agent import run_agent, route_request_intent, AgentResponse
from agent.chains import format_conversation_history
from agent.ollama_client import OllamaClient


# =====================================================================
# Offline Unit Tests (Run in normal CI without Ollama dependency)
# =====================================================================

def test_greeting_routing():
    """Test 1 & 2: Greetings route to general intent."""
    assert route_request_intent("hello") == "general"
    assert route_request_intent("hi") == "general"
    assert route_request_intent("hey there") == "general"
    assert route_request_intent("good morning") == "general"


def test_technical_and_specialized_routing():
    """Test 3-6: Technical and specialized route intent mapping."""
    assert route_request_intent("What is a pump?") == "general"
    assert route_request_intent("Explain this P&ID") == "pid"
    assert route_request_intent("What does API 610 say?") == "knowledge"
    assert route_request_intent("Create an Excel report") == "document"


def test_empty_input_status():
    """Test 7: Empty input returns needs_input status without LLM execution."""
    with patch("agent.graph.nodes.run_agent_request") as mock_chain:
        res = run_agent("")
        assert res.status == "needs_input"
        assert "cannot be empty" in res.answer
        mock_chain.assert_not_called()


def test_general_response_delegates_history():
    """Test 8 & 9: Verify general_response passes bounded conversation history to run_agent_request."""
    history = [
        {"role": "user", "content": "What is a pump?"},
        {"role": "assistant", "content": "A pump moves fluids."},
    ]
    mock_res = AgentResponse(answer="It is used for fluid transfer.", status="success", sources=[])

    with patch("agent.graph.nodes.run_agent_request", return_value=mock_res) as mock_req:
        res = run_agent("Why is it used?", conversation_history=history)
        assert res.status == "success"
        assert res.answer == "It is used for fluid transfer."
        mock_req.assert_called_once()
        _, kwargs = mock_req.call_args
        assert kwargs.get("conversation_history") == history


def test_history_bounding_formatter():
    """Test 9: Verify format_conversation_history bounds history to last 10 messages."""
    long_history = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    formatted = format_conversation_history(long_history, max_messages=10)
    assert len(formatted) == 10
    assert formatted[0].content == "msg 10"
    assert formatted[-1].content == "msg 19"


def test_no_chain_of_thought_in_state():
    """Test 10: Verify state responses contain clean answer strings without raw reasoning artifacts."""
    mock_res = AgentResponse(answer="Centrifugal pumps rely on rotational energy.", status="success", sources=[])
    with patch("agent.graph.nodes.run_agent_request", return_value=mock_res):
        res = run_agent("Explain centrifugal pumps")
        assert res.answer == "Centrifugal pumps rely on rotational energy."
        assert "<think>" not in res.answer


# =====================================================================
# Live Integration Tests (Require live Ollama service)
# =====================================================================


@pytest.mark.integration
def test_conversation_live_greetings(ollama_check):
    """Integration test: Verify live natural greeting generation."""
    res = run_agent("Hello")
    assert res.status == "success"
    assert isinstance(res.answer, str)
    assert len(res.answer) > 2


@pytest.mark.integration
def test_conversation_live_multiturn(ollama_check):
    """Integration test: Verify multi-turn conversation with history context."""
    # Turn 1
    res1 = run_agent("What is a pump?")
    assert res1.status == "success"
    assert "pump" in res1.answer.lower()

    history = [
        {"role": "user", "content": "What is a pump?"},
        {"role": "assistant", "content": res1.answer},
    ]

    # Turn 2
    res2 = run_agent("Why is it used in process plants?", conversation_history=history)
    assert res2.status in ("success", "error")
    assert len(res2.answer) > 10

    if res2.status == "success":
        history.append({"role": "user", "content": "Why is it used in process plants?"})
        history.append({"role": "assistant", "content": res2.answer})

        # Turn 3
        res3 = run_agent("Explain that in simple terms.", conversation_history=history)
        assert res3.status in ("success", "error")
        assert len(res3.answer) > 5
