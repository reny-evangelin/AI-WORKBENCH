"""
nodes.py — LangGraph Workflow Nodes for Member 2 Agent
"""

from typing import Dict, Any, List
from .state import AgentState
from .router import route_request_intent
from ..chains import run_agent_request
from ..tools import tool_registry

MAX_ITERATIONS = 5


def validate_input(state: AgentState) -> Dict[str, Any]:
    """Node: Validates user input and rejects empty or whitespace requests early without calling LLM."""
    raw_req = state.get("user_request", "")
    clean_req = raw_req.strip() if raw_req else ""

    if not clean_req:
        return {
            "user_request": "",
            "status": "needs_input",
            "route": None,
            "response": "User request cannot be empty. Please provide a valid engineering query.",
            "sources": [],
            "messages": state.get("messages", []),
            "iteration_count": 0,
            "observations": [],
            "plan": [],
        }

    return {
        "user_request": clean_req,
        "status": "ready",
        "sources": state.get("sources", []),
        "messages": state.get("messages", []),
        "iteration_count": 0,
        "observations": [],
        "plan": [],
        "current_step": 0,
    }


def plan_request(state: AgentState) -> Dict[str, Any]:
    """Node: Analyzes user request and creates a structured execution plan."""
    user_req = state.get("user_request", "")
    route = route_request_intent(user_req)

    # Detect multi-step intent (e.g. P&ID + Excel generation)
    lower = user_req.lower()
    if ("p&id" in lower or "pid" in lower) and ("excel" in lower or "report" in lower):
        plan = [
            {"step": 1, "action": "analyze_pid", "purpose": "Analyze P&ID drawing and extract components"},
            {"step": 2, "action": "generate_excel", "purpose": "Generate Excel report from extracted components"},
        ]
        intent = "multi_step"
    elif route == "pid":
        plan = [{"step": 1, "action": "analyze_pid", "purpose": "Analyze P&ID drawing"}]
        intent = "pid"
    elif route == "knowledge":
        plan = [{"step": 1, "action": "search_knowledge", "purpose": "Search engineering knowledge base"}]
        intent = "knowledge"
    elif route == "document":
        plan = [{"step": 1, "action": "generate_excel", "purpose": "Generate engineering document/report"}]
        intent = "document"
    else:
        plan = [{"step": 1, "action": "respond", "purpose": "Generate direct conversational/technical LLM answer"}]
        intent = "general"

    return {
        "route": route,
        "intent": intent,
        "plan": plan,
        "current_step": 1,
    }


def select_action(state: AgentState) -> Dict[str, Any]:
    """Node: Selects immediate operational action from the structured plan."""
    plan = state.get("plan", [])
    step_idx = state.get("current_step", 1) - 1

    if 0 <= step_idx < len(plan):
        action = plan[step_idx].get("action", "respond")
    else:
        action = "respond"

    if action == "respond":
        return {"tool_name": None, "tool_required": False}

    return {
        "tool_name": action,
        "tool_required": True,
        "tool_input": {"file_path": None, "query": state.get("user_request", "")},
    }


def execute_tool_node(state: AgentState) -> Dict[str, Any]:
    """Node: Safely executes registered tool from ToolRegistry."""
    tool_name = state.get("tool_name") or ""
    tool_input = state.get("tool_input") or {}

    # Check for missing inputs before executing tool
    if tool_name == "analyze_pid" and not tool_input.get("file_path"):
        obs = {
            "success": False,
            "tool_name": tool_name,
            "data": {},
            "sources": [],
            "error": "Missing required P&ID file path. Please provide the P&ID file.",
        }
    else:
        result = tool_registry.execute_tool(tool_name, tool_input)
        obs = result.model_dump()

    observations = list(state.get("observations", []))
    observations.append(obs)

    sources = list(state.get("sources", []))
    for src in obs.get("sources", []):
        if src not in sources:
            sources.append(src)

    return {
        "tool_result": obs,
        "observations": observations,
        "sources": sources,
    }


def evaluate_result(state: AgentState) -> Dict[str, Any]:
    """Node: Evaluates tool execution results and updates iteration counter / step progress."""
    count = state.get("iteration_count", 0) + 1
    if count >= MAX_ITERATIONS:
        return {
            "iteration_count": count,
            "status": "error",
            "response": "Execution stopped: maximum iteration limit (5) reached.",
        }

    plan = state.get("plan", [])
    current_step = state.get("current_step", 1)
    tool_res = state.get("tool_result", {})

    # If a required input was missing or tool failed, halt step progression gracefully
    if tool_res and not tool_res.get("success", False):
        error_msg = tool_res.get("error", "Tool execution failed.")
        return {
            "iteration_count": count,
            "status": "needs_input" if "Missing" in error_msg else "error",
            "response": error_msg,
        }

    next_step = current_step + 1
    if next_step > len(plan):
        # All planned steps completed
        return {
            "iteration_count": count,
            "status": "ready_to_finalize",
        }

    return {
        "iteration_count": count,
        "current_step": next_step,
        "status": "in_progress",
    }


def general_response(state: AgentState) -> Dict[str, Any]:
    """Node: Delegates general conversational and technical queries to LCEL pipeline."""
    user_req = state.get("user_request", "")
    history = state.get("messages", [])

    res = run_agent_request(user_req, conversation_history=history)

    updated_messages = list(history)
    updated_messages.append({"role": "user", "content": user_req})
    updated_messages.append({"role": "assistant", "content": res.answer})

    return {
        "response": res.answer,
        "status": res.status,
        "sources": res.sources,
        "messages": updated_messages,
    }


def finalize_agent_response(state: AgentState) -> Dict[str, Any]:
    """Node: Normalizes final output state and formats multi-step tool observation summaries."""
    if state.get("response"):
        return {
            "response": state["response"],
            "status": state.get("status") or "success",
            "sources": state.get("sources", []),
        }

    obs_list = state.get("observations", [])
    if obs_list:
        summaries = []
        for obs in obs_list:
            t_name = obs.get("tool_name", "tool")
            if obs.get("success"):
                d_status = obs.get("data", {}).get("status") or obs.get("data", {}).get("summary") or "completed successfully"
                summaries.append(f"[{t_name}]: {d_status}")
            else:
                summaries.append(f"[{t_name} error]: {obs.get('error')}")

        resp_text = "\n".join(summaries)
        status = "success" if any(o.get("success") for o in obs_list) else "error"
    else:
        resp_text = "No response generated."
        status = state.get("status") or "success"

    return {
        "response": resp_text,
        "status": status,
        "sources": state.get("sources", []),
    }
