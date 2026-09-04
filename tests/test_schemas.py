"""
test_schemas.py — Offline unit tests for AgentRequest and AgentResponse schemas
"""

import pytest
from agent.schemas import AgentRequest, AgentResponse


def test_agent_request_valid():
    """Verify AgentRequest accepts valid non-empty string."""
    req = AgentRequest(user_request="What is a centrifugal pump?")
    assert req.user_request == "What is a centrifugal pump?"


def test_agent_request_whitespace_stripping():
    """Verify AgentRequest strips leading and trailing whitespace."""
    req = AgentRequest(user_request="   Check valve specs   ")
    assert req.user_request == "Check valve specs"


def test_agent_request_empty_raises():
    """Verify AgentRequest raises ValueError on empty or whitespace string."""
    with pytest.raises(ValueError, match="cannot be empty"):
        AgentRequest(user_request="")

    with pytest.raises(ValueError, match="cannot be empty"):
        AgentRequest(user_request="   ")


def test_agent_response_defaults():
    """Verify AgentResponse default fields."""
    res = AgentResponse(answer="Pump P-101 is an inline centrifugal pump.")
    assert res.answer == "Pump P-101 is an inline centrifugal pump."
    assert res.status == "success"
    assert res.sources == []


def test_agent_response_custom_status_and_sources():
    """Verify AgentResponse with custom status and sources list."""
    res = AgentResponse(
        answer="Missing P&ID diagram.",
        status="needs_input",
        sources=["doc_1.pdf"],
    )
    assert res.status == "needs_input"
    assert res.sources == ["doc_1.pdf"]
