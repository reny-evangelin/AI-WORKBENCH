"""
workflow.py — LangGraph Orchestration for Member 2 Agent
"""
import logging
from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import (
    validate_input,
    process_vision,
    understand_request,
    select_action,
    execute_tool_node,
    evaluate_result,
    synthesize_rag,
    finalize_agent_response,
)

logger = logging.getLogger("agent")


def route_after_validation(state: AgentState) -> str:
    """Conditional router following input validation."""
    if state.get("status") == "needs_input":
        return "invalid"
    if state.get("vision_input"):
        return "vision"
    return "valid"


def route_action_choice(state: AgentState) -> str:
    """Conditional router following action selection."""
    if state.get("tool_required"):
        return "tool"
    return "respond"


def route_loop_eval(state: AgentState) -> str:
    """Conditional router following evaluation of tool execution results."""
    intent = state.get("intent", "")
    st = state.get("status")
    
    # If the intent requires synthesizing the RAG output with an LLM
    if st == "ready_to_finalize" and intent == "rag":
        return "synthesize"
        
    return "finish"


def build_agent_graph():
    """Constructs and compiles the unified 1-LLM-call LangGraph Workflow."""
    workflow = StateGraph(AgentState)

    # 1. Add nodes
    workflow.add_node("validate_input", validate_input)
    workflow.add_node("process_vision", process_vision)
    workflow.add_node("understand_request", understand_request)
    workflow.add_node("select_action", select_action)
    workflow.add_node("execute_tool_node", execute_tool_node)
    workflow.add_node("evaluate_result", evaluate_result)
    workflow.add_node("synthesize_rag", synthesize_rag)
    workflow.add_node("finalize_agent_response", finalize_agent_response)

    # 2. Add edges and conditional routing
    workflow.add_edge(START, "validate_input")

    workflow.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {
            "invalid": "finalize_agent_response",
            "vision": "process_vision",
            "valid": "understand_request"
        }
    )

    workflow.add_edge("process_vision", "understand_request")
    workflow.add_edge("understand_request", "select_action")

    workflow.add_conditional_edges(
        "select_action",
        route_action_choice,
        {
            "tool": "execute_tool_node",
            "respond": "finalize_agent_response"
        }
    )

    workflow.add_edge("execute_tool_node", "evaluate_result")

    workflow.add_conditional_edges(
        "evaluate_result",
        route_loop_eval,
        {
            "synthesize": "synthesize_rag",
            "finish": "finalize_agent_response"
        }
    )

    workflow.add_edge("synthesize_rag", "finalize_agent_response")
    workflow.add_edge("finalize_agent_response", END)

    return workflow.compile()

# Singleton compiled graph instance
agent_graph = build_agent_graph()

def process_request(user_request: str, image_path: str = None, callbacks=None, conversation_history=None):
    from ..schemas import AgentResponse
    logger.info(f"--- STARTING REQUEST PROCESS: {user_request} ---")

    initial_state = AgentState(
        user_request=user_request,
        vision_input=image_path,
        vision_result=None,
        status="initializing",
        intent=None,
        tool_required=False,
        messages=list(conversation_history) if conversation_history else [],
        sources=[],
        observations=[],
        iteration_count=0,
        error=None,
        metrics={},
        brain_decision={}
    )

    try:
        final_state = agent_graph.invoke(
            initial_state, 
            config={"recursion_limit": 25, "callbacks": callbacks}
        )
        
        # Log performance
        metrics = final_state.get("metrics", {})
        total_time = sum(metrics.values())
        logger.info(f"--- REQUEST COMPLETE in {total_time:.1f}ms ---")
        if metrics:
            logger.info(f"Metrics: {metrics}")
            
        return AgentResponse(
            answer=final_state.get("response", "No answer generated."),
            status=final_state.get("status", "error"),
            sources=final_state.get("sources", [])
        )
    except Exception as e:
        logger.error(f"Graph execution failed: {e}", exc_info=True)
        return AgentResponse(
            answer=f"A critical system error occurred during execution: {str(e)}",
            status="error",
            sources=[]
        )
