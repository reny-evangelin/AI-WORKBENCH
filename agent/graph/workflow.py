"""
workflow.py — LangGraph Agentic Workflow Construction and Public Entrypoint
"""

from typing import Optional, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import (
    validate_input,
    detect_intent,
    plan_request,
    generate_content,
    select_action,
    execute_tool_node,
    evaluate_result,
    general_response,
    finalize_agent_response,
)
from ..schemas import AgentResponse


def check_input_validity(state: AgentState) -> str:
    """Conditional router following input validation."""
    if state.get("status") == "needs_input":
        return "invalid"
    return "valid"


def route_action_choice(state: AgentState) -> str:
    """Conditional router following action selection."""
    if state.get("tool_required"):
        return "tool"
    return "respond"


def route_loop_eval(state: AgentState) -> str:
    """Conditional router following evaluation of tool execution results."""
    st = state.get("status")
    if st == "in_progress":
        return "next_step"
    return "finish"


def build_agent_graph():
    """Constructs and compiles the Member 2 LangGraph Agentic Reason → Act → Observe Workflow."""
    workflow = StateGraph(AgentState)

    # 1. Add nodes
    workflow.add_node("validate_input", validate_input)
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("plan_request", plan_request)
    workflow.add_node("generate_content", generate_content)
    workflow.add_node("select_action", select_action)
    workflow.add_node("execute_tool_node", execute_tool_node)
    workflow.add_node("evaluate_result", evaluate_result)
    workflow.add_node("general_response", general_response)
    workflow.add_node("finalize_agent_response", finalize_agent_response)

    # 2. Add edges and conditional routing
    workflow.add_edge(START, "validate_input")

    workflow.add_conditional_edges(
        "validate_input",
        check_input_validity,
        {
            "invalid": END,
            "valid": "detect_intent",
        },
    )

    workflow.add_edge("detect_intent", "plan_request")
    workflow.add_edge("plan_request", "generate_content")
    workflow.add_edge("generate_content", "select_action")

    workflow.add_conditional_edges(
        "select_action",
        route_action_choice,
        {
            "tool": "execute_tool_node",
            "respond": "general_response",
        },
    )

    workflow.add_edge("execute_tool_node", "evaluate_result")

    workflow.add_conditional_edges(
        "evaluate_result",
        route_loop_eval,
        {
            "next_step": "select_action",
            "finish": "finalize_agent_response",
        },
    )

    workflow.add_edge("general_response", "finalize_agent_response")
    workflow.add_edge("finalize_agent_response", END)

    return workflow.compile()


# Singleton compiled graph instance
agent_graph = build_agent_graph()


def run_agent(
    user_request: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> AgentResponse:
    """Public application entrypoint for executing the Member 2 Agentic LangGraph workflow.

    Supports optional conversation_history list of dicts: [{'role': 'user'|'assistant', 'content': '...'}]
    Returns a structured AgentResponse instance.
    """
    initial_state: AgentState = {
        "user_request": user_request,
        "status": "pending",
        "route": None,
        "intent": None,
        "plan": [],
        "current_step": 0,
        "tool_name": None,
        "tool_input": None,
        "tool_result": None,
        "observations": [],
        "context": None,
        "messages": list(conversation_history) if conversation_history else [],
        "response": None,
        "sources": [],
        "tool_required": False,
        "error": None,
        "iteration_count": 0,
    }

    final_state = agent_graph.invoke(initial_state)

    ans = final_state.get("response") or "No response generated."
    st = final_state.get("status") or "success"
    src = final_state.get("sources") or []

    return AgentResponse(
        answer=ans,
        status=st,
        sources=src,
    )
