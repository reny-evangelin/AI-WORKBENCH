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
    image_path: Optional[str] = Field(
        default=None,
        description="Optional path to an uploaded image for vision processing."
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


class ExcelFormula(BaseModel):
    column: str = Field(..., description="The name of the column where the formula will be placed.")
    formula: str = Field(..., description="The formula string, e.g., '=SUM(B{row}:D{row})'")

class ExcelSheetData(BaseModel):
    name: str = Field(..., description="The name of the worksheet.")
    columns: List[str] = Field(..., description="Ordered list of column header names.")
    rows: List[Dict[str, Any]] = Field(..., description="Data rows mapped to column names.")
    formulas: List[ExcelFormula] = Field(default_factory=list, description="Formulas to inject into rows.")

class ExcelPlan(BaseModel):
    filename: str = Field(..., description="A safe .xlsx filename based on the user request.")
    title: Optional[str] = Field(default=None, description="Title of the report.")
    sheets: List[ExcelSheetData] = Field(..., description="List of sheets to generate in the workbook.")


class DocSection(BaseModel):
    heading: str = Field(..., description="Section Name")
    content: str = Field(..., description="Detailed paragraph content for the section")

class DocumentPlan(BaseModel):
    title: str = Field(..., description="Document Title")
    sections: List[DocSection] = Field(..., description="List of document sections.")


class BrainDecision(BaseModel):
    """Structured LLM planning decision returned by the central Brain."""
    
    intent: Literal["chat", "rag", "excel", "pdf", "docx", "error"] = Field(
        ..., 
        description="The type of action required."
    )
    
    direct_response: Optional[str] = Field(
        default=None, 
        description="The direct answer to the user's question, populated ONLY if intent is 'chat'."
    )
    
    search_query: Optional[str] = Field(
        default=None, 
        description="The focused search query to retrieve information, populated ONLY if intent is 'rag'."
    )
    
    excel_plan: Optional[ExcelPlan] = Field(
        default=None, 
        description="The complete structured plan for generating the Excel workbook, populated ONLY if intent is 'excel'."
    )
    
    document_plan: Optional[DocumentPlan] = Field(
        default=None, 
        description="The structured plan for generating a PDF or DOCX document, populated ONLY if intent is 'pdf' or 'docx'."
    )
