import pytest
from agent.graph.state import AgentState
from agent.graph.workflow import route_action_choice, route_loop_eval, check_input_validity
from agent.graph.nodes import select_action

def test_check_input_validity():
    assert check_input_validity({"status": "needs_input"}) == "invalid"
    assert check_input_validity({"status": "ready"}) == "valid"

def test_route_action_choice():
    assert route_action_choice({"tool_required": True}) == "tool"
    assert route_action_choice({"tool_required": False}) == "respond"

def test_route_loop_eval():
    assert route_loop_eval({"status": "ready_to_finalize", "intent": "rag"}) == "synthesize"
    assert route_loop_eval({"status": "ready_to_finalize", "intent": "excel"}) == "finish"
    assert route_loop_eval({"status": "error", "intent": "pdf"}) == "finish"

def test_select_action_excel():
    state = {
        "user_request": "Make excel",
        "brain_decision": {
            "intent": "excel",
            "excel_plan": {"filename": "test.xlsx", "sheets": []}
        }
    }
    result = select_action(state)
    assert result["tool_name"] == "generate_excel"
    assert result["tool_required"] is True
    assert "test.xlsx" in str(result["tool_input"])

def test_select_action_rag():
    state = {
        "user_request": "How does it work?",
        "brain_decision": {
            "intent": "rag",
            "search_query": "how it works"
        }
    }
    result = select_action(state)
    assert result["tool_name"] == "search_knowledge"
    assert result["tool_required"] is True
    assert result["tool_input"]["query"] == "how it works"

def test_select_action_chat():
    state = {
        "user_request": "Hello",
        "brain_decision": {
            "intent": "chat",
            "direct_response": "Hi there"
        }
    }
    result = select_action(state)
    assert result["tool_name"] is None
    assert result["tool_required"] is False
