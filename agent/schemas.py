"""
schemas.py — Application Request, Response, and Decision Schemas for Member 2 Agent
"""

from typing import List, Literal, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class AgentRequest(BaseModel):
    """Structured container for incoming user agent requests."""

    user_request: str = Field(
        ...,
        description="User query or instruction for the AI Engineering Assistant.",
    )

    @field_validator("user_request")
    @classmethod
    def validate_user_request(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("User request cannot be empty or only whitespace.")
        return stripped


class AgentResponse(BaseModel):
    """Structured application-level response returned by the agent."""

    answer: str = Field(
        ...,
        description="The response content or summary from the agent.",
    )
    status: Literal["success", "needs_input", "error"] = Field(
        default="success",
        description="Execution status: success, needs_input, or error.",
    )
    sources: List[str] = Field(
        default_factory=list,
        description="List of source references used in generating the answer.",
    )


class PlanStep(BaseModel):
    """Single step in an agentic execution plan."""

    step: int = Field(..., description="Step index number.")
    action: str = Field(..., description="Operational action to perform.")
    purpose: str = Field(..., description="Objective or purpose of this step.")


class AgentDecision(BaseModel):
    """Structured LLM planning decision returned by the reasoning brain."""

    intent: str = Field(..., description="Classified request intent.")
    goal: str = Field(..., description="High-level goal statement.")
    plan: List[PlanStep] = Field(
        default_factory=list,
        description="Structured operational plan steps.",
    )
    next_action: str = Field(
        default="respond",
        description="Immediate next action: respond, analyze_pid, search_knowledge, generate_pdf, generate_docx, generate_excel.",
    )
    tool_required: bool = Field(
        default=False,
        description="True if tool execution is required for the next action.",
    )
    tool_input: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters for the required tool.",
    )
