"""
test_agentic.py — Offline Unit and Live Integration tests for Phase 3 Agentic Engine
"""

import pytest
from unittest.mock import patch, MagicMock
from agent import run_agent, AgentResponse, tool_registry
from agent.tools import ToolResult
from agent.graph.nodes import plan_request, execute_tool_node, evaluate_result, MAX_ITERATIONS
from agent.ollama_client import OllamaClient


# =====================================================================
# Offline Unit Tests (Run in CI without network/Ollama dependencies)
# =====================================================================

def test_conversational_response_planning():
    """Test 1: Hello routes to direct conversational response."""
    state = {"user_request": "hello"}
    res = plan_request(state)
    assert res["intent"] == "general"
    assert res["plan"][0]["action"] == "respond"


def test_general_query_planning():
    """Test 2: General question routes to direct LLM response path."""
    state = {"user_request": "What is a pump?"}
    res = plan_request(state)
    assert res["intent"] == "general"
    assert res["plan"][0]["action"] == "respond"


def test_pid_action_planning():
    """Test 3: P&ID request produces analyze_pid plan action."""
    state = {"user_request": "Explain this P&ID drawing"}
    res = plan_request(state)
    assert res["intent"] == "pid"
    assert res["plan"][0]["action"] == "analyze_pid"


def test_excel_action_planning():
    """Test 4: Excel report request produces generate_excel plan action."""
    state = {"user_request": "Create an Excel report"}
    res = plan_request(state)
    assert res["intent"] == "document"
    assert res["plan"][0]["action"] == "generate_excel"


def test_multistep_plan_creation():
    """Test 5: Multi-step request produces sequential multi-step plan."""
    state = {"user_request": "Analyze this P&ID and create an Excel report"}
    res = plan_request(state)
    assert res["intent"] == "multi_step"
    assert len(res["plan"]) == 2
    assert res["plan"][0]["action"] == "analyze_pid"
    assert res["plan"][1]["action"] == "generate_excel"


def test_missing_input_detection():
    """Test 6: Missing P&ID file input halts tool execution gracefully with needs_input."""
    state = {
        "user_request": "Analyze my P&ID",
        "tool_name": "analyze_pid",
        "tool_input": {"file_path": None},
        "observations": [],
        "sources": [],
    }
    obs_res = execute_tool_node(state)
    assert obs_res["tool_result"]["success"] is False
    assert "Missing" in obs_res["tool_result"]["error"]

    state["tool_result"] = obs_res["tool_result"]
    eval_res = evaluate_result(state)
    assert eval_res["status"] == "needs_input"


def test_tool_failure_recovery():
    """Test 7: ToolResult failure returns controlled error status."""
    with patch.object(tool_registry, "execute_tool") as mock_exec:
        mock_exec.return_value = ToolResult(
            success=False,
            tool_name="search_knowledge",
            data={},
            sources=[],
            error="Database connection timeout",
        )
        state = {
            "user_request": "Search knowledge",
            "tool_name": "search_knowledge",
            "tool_input": {"query": "API 610"},
            "observations": [],
            "sources": [],
        }
        res = execute_tool_node(state)
        assert res["tool_result"]["success"] is False
        assert "timeout" in res["tool_result"]["error"]


def test_max_iteration_limit_enforcement():
    """Test 8: Maximum iteration count stops execution loop safely."""
    state = {"iteration_count": MAX_ITERATIONS - 1, "plan": [], "current_step": 1}
    res = evaluate_result(state)
    assert res["status"] == "error"
    assert "maximum iteration limit" in res["response"]


def test_arbitrary_tool_execution_rejection():
    """Test 10: Arbitrary tool or shell command execution is rejected by registry."""
    res_shell = tool_registry.execute_tool("shell", {"command": "dir"})
    assert res_shell.success is False
    assert "Unauthorized tool execution" in res_shell.error

    res_powershell = tool_registry.execute_tool("powershell", {"command": "ls"})
    assert res_powershell.success is False
    assert "Unauthorized tool execution" in res_powershell.error


# =====================================================================
# Live Integration Tests (Require live Ollama service)
# =====================================================================


@pytest.mark.integration
def test_agentic_live_general_execution(ollama_check):
    """Integration test: Verify live general query execution via agentic workflow."""
    res = run_agent("What is a pump?")
    assert res.status == "success"
    assert isinstance(res.answer, str)
    assert len(res.answer) > 10


@pytest.mark.integration
def test_agentic_live_multistep_honest_response(ollama_check):
    """Integration test: Multi-step request produces honest response without fake data."""
    res = run_agent("Analyze this P&ID drawing and create an Excel report")
    assert res.status in ("needs_input", "error", "success")
    assert isinstance(res.answer, str)
