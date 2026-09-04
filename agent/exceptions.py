"""
exceptions.py — Custom Exceptions for Member 2 Agent
"""


class AgentError(Exception):
    """Base exception for all agent domain errors."""

    pass


class InvalidInputError(AgentError):
    """Raised when user request input is invalid or empty."""

    pass


class OllamaConnectionError(AgentError):
    """Raised when Ollama LLM service is unreachable or errors out."""

    pass


class ChainExecutionError(AgentError):
    """Raised when LCEL chain execution encounters an error."""

    pass
