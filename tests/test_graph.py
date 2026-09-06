"""
test_graph.py — Unit and Integration tests for LangGraph Agent Workflow
"""

import pytest
from unittest.mock import patch
from agent.schemas import AgentResponse
from agent.graph.workflow import route_action_choice
from agent.graph.workflow import build_agent_graph, process_request
from agent.ollama_client import OllamaClient


# =====================================================================
# Unit Tests (Offline safe — run in normal CI)
# =====================================================================

"""
test_graph.py — Unit and Integration tests for LangGraph Agent Workflow
"""

import pytest
from unittest.mock import patch
from agent.schemas import AgentResponse
from agent.graph.workflow import build_agent_graph, process_request

# =====================================================================
# Unit Tests (Offline safe — run in normal CI)
# =====================================================================

def test_graph_compilation():
    """Verify that the LangGraph workflow compiles successfully."""
    graph = build_agent_graph()
    assert graph is not None


def test_empty_input_routing():
    """Test 1: Empty input returns needs_input status without calling LLM."""
    with patch("agent.graph.nodes.get_llm") as mock_llm:
        res = process_request("")
        assert res.status == "needs_input"
        assert "cannot be empty" in res.answer
        mock_llm.assert_not_called()


from agent.graph.workflow import route_after_validation, route_action_choice, route_loop_eval

def test_route_after_validation():
    assert route_after_validation({"status": "needs_input"}) == "invalid"
    assert route_after_validation({"status": "initializing"}) == "valid"

def test_route_action_choice():
    assert route_action_choice({"tool_required": True}) == "tool"
    assert route_action_choice({"tool_required": False}) == "respond"

def test_route_loop_eval():
    assert route_loop_eval({"status": "ready_to_finalize", "intent": "rag"}) == "synthesize"
    assert route_loop_eval({"status": "ready_to_finalize", "intent": "chat"}) == "finish"
    assert route_loop_eval({"status": "error", "intent": "rag"}) == "finish"


def test_planner_json_failure_with_fallback():
    from agent.graph.nodes import understand_request
    from langchain_core.messages import AIMessage

    class MockLLM:
        def bind(self, *args, **kwargs):
            return self
            
        def invoke(self, *args, **kwargs):
            return AIMessage(content="I am a bad LLM and I refuse to output JSON!")

    with patch("agent.graph.nodes.get_llm", return_value=MockLLM()):
        # 1. Obvious intent - SmartRouter fallback should catch it
        state1 = {"user_request": "generate an Excel report for the pumps", "intent": None}
        result1 = understand_request(state1)
        assert result1["intent"] == "excel"
        assert result1["brain_decision"]["intent"] == "excel"
        assert "excel_plan" in result1["brain_decision"]
        
        # 2. Complete gibberish - Fallback should error gracefully, not crash
        state2 = {"user_request": "asdfasdfasdf", "intent": None}
        result2 = understand_request(state2)
        assert result2["intent"] == "error"
        assert "internal error" in result2["brain_decision"]["direct_response"]


# =====================================================================
# Integration Tests (Require live Ollama service)
# =====================================================================

@pytest.mark.integration
def test_process_request_integration_general_query(ollama_check):
    """Integration test: Verify live end-to-end execution of process_request via LangGraph."""
    res = process_request("What is the purpose of a pump in a process plant?")
    assert res.status in ("success", "error")
    assert isinstance(res.answer, str)
