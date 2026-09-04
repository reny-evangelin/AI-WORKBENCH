"""
Member 2 — Main AI Agent Package
"""

from .config import Settings, settings
from .ollama_client import OllamaClient
from .llm import get_llm
from .prompts import ENGINEERING_SYSTEM_PROMPT, get_engineering_prompt_template
from .schemas import AgentRequest, AgentResponse, PlanStep, AgentDecision
from .chains import create_agent_chain, run_agent_request
from .exceptions import (
    AgentError,
    InvalidInputError,
    OllamaConnectionError,
    ChainExecutionError,
)
from .graph import AgentState, run_agent, agent_graph, route_request_intent
from .tools import ToolResult, ToolRegistry, tool_registry

__all__ = [
    "Settings",
    "settings",
    "OllamaClient",
    "get_llm",
    "ENGINEERING_SYSTEM_PROMPT",
    "get_engineering_prompt_template",
    "AgentRequest",
    "AgentResponse",
    "PlanStep",
    "AgentDecision",
    "create_agent_chain",
    "run_agent_request",
    "AgentState",
    "run_agent",
    "agent_graph",
    "route_request_intent",
    "ToolResult",
    "ToolRegistry",
    "tool_registry",
    "AgentError",
    "InvalidInputError",
    "OllamaConnectionError",
    "ChainExecutionError",
]
