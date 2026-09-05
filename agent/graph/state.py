"""
state.py — LangGraph Agentic State Definition
"""

from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict, total=False):
    """LangGraph state representation for Member 2 Agentic workflow."""

    user_request: str
    status: str
    route: Optional[str]
    intent: Optional[str]
    document_type: Optional[str]
    plan: List[Dict[str, Any]]
    current_step: int
    tool_name: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    generated_content: Optional[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    observations: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]]
    messages: List[Dict[str, str]]
    response: Optional[str]
    sources: List[str]
    tool_required: bool
    error: Optional[str]
    iteration_count: int
