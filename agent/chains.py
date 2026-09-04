"""
chains.py — LangChain Application Chains and Agent Request Handler
"""

from typing import Optional, Union, List, Dict, Any
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from .config import Settings
from .llm import get_llm
from .prompts import get_engineering_prompt_template
from .schemas import AgentRequest, AgentResponse


def create_agent_chain(config: Optional[Settings] = None):
    """Constructs the core LCEL chain: Prompt | ChatOllama | StrOutputParser."""
    prompt = get_engineering_prompt_template()
    llm = get_llm(config)
    output_parser = StrOutputParser()
    return prompt | llm | output_parser


def format_conversation_history(
    history: Optional[List[Union[Dict[str, str], BaseMessage]]],
    max_messages: int = 10,
) -> List[BaseMessage]:
    """Converts and bounds conversation history list into LangChain BaseMessage objects."""
    if not history:
        return []

    # Bound to last N messages
    bounded = history[-max_messages:]
    formatted: List[BaseMessage] = []

    for msg in bounded:
        if isinstance(msg, BaseMessage):
            formatted.append(msg)
        elif isinstance(msg, dict):
            role = msg.get("role", "user").lower()
            content = msg.get("content", "")
            if role in ("user", "human"):
                formatted.append(HumanMessage(content=content))
            elif role in ("assistant", "ai"):
                formatted.append(AIMessage(content=content))

    return formatted


def run_agent_request(
    user_request: Union[str, AgentRequest],
    config: Optional[Settings] = None,
    conversation_history: Optional[List[Union[Dict[str, str], BaseMessage]]] = None,
    max_history_messages: int = 10,
) -> AgentResponse:
    """Application-level entrypoint for processing user queries with optional conversation history.

    Returns an AgentResponse with status 'success', 'needs_input', or 'error'.
    Never crashes with unhandled raw model exceptions.
    """
    # 1. Parse and validate input
    if isinstance(user_request, AgentRequest):
        raw_text = user_request.user_request
    elif isinstance(user_request, str):
        raw_text = user_request
    else:
        return AgentResponse(
            answer="Invalid request format provided.",
            status="needs_input",
            sources=[],
        )

    clean_text = raw_text.strip() if raw_text else ""
    if not clean_text:
        return AgentResponse(
            answer="User request cannot be empty. Please provide a valid engineering query.",
            status="needs_input",
            sources=[],
        )

    # 2. Format bounded history
    history_messages = format_conversation_history(
        conversation_history, max_messages=max_history_messages
    )

    # 3. Construct and invoke LCEL chain
    try:
        chain = create_agent_chain(config)
        result_text = chain.invoke(
            {
                "user_request": clean_text,
                "history": history_messages,
            }
        )
        return AgentResponse(
            answer=str(result_text).strip(),
            status="success",
            sources=[],
        )
    except Exception as e:
        error_msg = str(e)
        if "Connection" in error_msg or "refused" in error_msg or "timeout" in error_msg.lower():
            return AgentResponse(
                answer=f"Unable to connect to Ollama LLM service: {error_msg}",
                status="error",
                sources=[],
            )
        return AgentResponse(
            answer=f"Agent execution encountered an error: {error_msg}",
            status="error",
            sources=[],
        )
