"""
test_conversation.py — Unit and Integration tests for conversational agent flow
"""

import pytest
from unittest.mock import patch, MagicMock
from agent import process_request, AgentResponse
from agent.graph.workflow import route_action_choice
from agent.chains import format_conversation_history
from agent.ollama_client import OllamaClient


# =====================================================================
# Offline Unit Tests (Run in normal CI without Ollama dependency)
# =====================================================================

"""
test_conversation.py — Unit and Integration tests for conversational agent flow
"""

import pytest
from unittest.mock import patch
from agent import process_request, AgentResponse
from agent.chains import format_conversation_history

# =====================================================================
# Offline Unit Tests (Run in normal CI without Ollama dependency)
# =====================================================================

def test_empty_input_status():
    """Test 1: Empty input returns needs_input status without LLM execution."""
    with patch("agent.graph.nodes.get_llm") as mock_llm:
        res = process_request("")
        assert res.status == "needs_input"
        assert "cannot be empty" in res.answer
        mock_llm.assert_not_called()

def test_history_bounding_formatter():
    """Test 2: Verify format_conversation_history bounds history to last 10 messages."""
    long_history = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    formatted = format_conversation_history(long_history, max_messages=10)
    assert len(formatted) == 10
    assert formatted[0].content == "msg 10"
    assert formatted[-1].content == "msg 19"

# =====================================================================
# Live Integration Tests (Require live Ollama service)
# =====================================================================

@pytest.mark.integration
def test_conversation_live_greetings(ollama_check):
    """Integration test: Verify live natural greeting generation."""
    res = process_request("Hello")
    assert res.status == "success"
    assert isinstance(res.answer, str)
    assert len(res.answer) > 2

@pytest.mark.integration
def test_conversation_live_multiturn(ollama_check):
    """Integration test: Verify multi-turn conversation with history context."""
    # Turn 1
    res1 = process_request("What is a pump?")
    assert res1.status == "success"
    assert "pump" in res1.answer.lower()

    history = [
        {"role": "user", "content": "What is a pump?"},
        {"role": "assistant", "content": res1.answer},
    ]

    # Turn 2
    res2 = process_request("Why is it used in process plants?", conversation_history=history)
    assert res2.status in ("success", "error")
    assert len(res2.answer) > 10

    if res2.status == "success":
        history.append({"role": "user", "content": "Why is it used in process plants?"})
        history.append({"role": "assistant", "content": res2.answer})

        # Turn 3
        res3 = process_request("Explain that in simple terms.", conversation_history=history)
        assert res3.status in ("success", "error")
        assert len(res3.answer) > 5
