"""
interfaces.py — Tool Result Schema and Interface Stubs for Member Capabilities
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Structured result returned by registered tool execution."""

    success: bool = Field(
        ...,
        description="Indicates whether tool execution succeeded.",
    )
    tool_name: str = Field(
        ...,
        description="Name of the executed tool.",
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Output data payload returned by the tool.",
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Source references associated with the tool result.",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if tool execution failed.",
    )


# =====================================================================
# Tool Interface Stubs (Member 1, Member 3, Member 4 placeholders)
# =====================================================================

def analyze_pid_stub(file_path: Optional[str] = None, **kwargs) -> ToolResult:
    """Stub for Member 1 P&ID analysis / OCR capabilities."""
    if not file_path:
        return ToolResult(
            success=False,
            tool_name="analyze_pid",
            data={},
            sources=[],
            error="Missing required P&ID file path or document input.",
        )
    return ToolResult(
        success=True,
        tool_name="analyze_pid",
        data={
            "summary": "P&ID analyzed (Member 1 stub)",
            "file": file_path,
            "components": ["P-101 (Centrifugal Pump)", "V-102 (Gate Valve)"],
        },
        sources=[f"{file_path}:p1"],
        error=None,
    )


def search_knowledge_stub(query: str, **kwargs) -> ToolResult:
    """Execute Member 3 RAG engineering knowledge base retrieval."""
    if not query or not query.strip():
        return ToolResult(
            success=False,
            tool_name="search_knowledge",
            data={},
            sources=[],
            error="Knowledge search query cannot be empty.",
        )
    try:
        from rag.retriever import retrieve
        matches = retrieve(query, n_results=3)
        sources = []
        snippets = []
        for m in matches:
            meta = m.get("metadata", {})
            src_file = meta.get("source_file") or meta.get("source", "knowledge_base")
            page = meta.get("page_number") or meta.get("page")
            src_ref = f"{src_file}:p{page}" if page is not None else str(src_file)
            if src_ref not in sources:
                sources.append(src_ref)
            snippets.append(m.get("text", "").strip())

        result_text = "\n\n".join(snippets) if snippets else "No matching engineering records found."
        return ToolResult(
            success=True,
            tool_name="search_knowledge",
            data={
                "query": query,
                "result": result_text,
                "matches": matches,
            },
            sources=sources,
            error=None,
        )
    except Exception as e:
        return ToolResult(
            success=False,
            tool_name="search_knowledge",
            data={},
            sources=[],
            error=f"Knowledge retrieval error: {str(e)}",
        )



import json
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DATA_PATH = PROJECT_ROOT / "data" / "sample_analysis.json"


def _get_analysis_data(content: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if content and isinstance(content, dict) and len(content) > 0:
        return content
    if SAMPLE_DATA_PATH.exists():
        with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"title": "Generated Report", "sections": [{"heading": "Content", "content": "No content provided."}]}

def _validate_file_output(file_path: Optional[str]) -> Dict[str, Any]:
    if not file_path:
        return {"file_exists": False, "size_bytes": 0}
    path = Path(file_path)
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return {"file_exists": exists, "size_bytes": size}

def generate_pdf_stub(content: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
    """Execute Member 4 PDF report generation."""
    try:
        from tools.output_generator import generate_outputs
        data = _get_analysis_data(content)
        output_dir = PROJECT_ROOT / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        result = generate_outputs(data, str(output_dir), formats=["pdf"])
        pdf_path = result.get("pdf")
        val = _validate_file_output(pdf_path)
        
        if not val["file_exists"] or val["size_bytes"] == 0:
             return ToolResult(
                success=False,
                tool_name="generate_pdf",
                data=val,
                sources=[],
                error="PDF generation failed: File was not created or is empty.",
            )
            
        return ToolResult(
            success=True,
            tool_name="generate_pdf",
            data={
                "status": "PDF report generation completed successfully",
                "file_path": pdf_path,
                "file_name": Path(pdf_path).name if pdf_path else "Approval_Note.pdf",
                **val
            },
            sources=[pdf_path] if pdf_path else [],
            error=None,
        )
    except Exception as e:
        return ToolResult(
            success=False,
            tool_name="generate_pdf",
            data={},
            sources=[],
            error=f"PDF generation failed: {str(e)}",
        )


def generate_docx_stub(content: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
    """Execute Member 4 DOCX report generation."""
    try:
        from tools.output_generator import generate_outputs
        data = _get_analysis_data(content)
        output_dir = PROJECT_ROOT / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        result = generate_outputs(data, str(output_dir), formats=["docx"])
        docx_path = result.get("docx")
        val = _validate_file_output(docx_path)
        
        if not val["file_exists"] or val["size_bytes"] == 0:
             return ToolResult(
                success=False,
                tool_name="generate_docx",
                data=val,
                sources=[],
                error="DOCX generation failed: File was not created or is empty.",
            )
            
        return ToolResult(
            success=True,
            tool_name="generate_docx",
            data={
                "status": "DOCX report generation completed successfully",
                "file_path": docx_path,
                "file_name": Path(docx_path).name if docx_path else "Approval_Note.docx",
                **val
            },
            sources=[docx_path] if docx_path else [],
            error=None,
        )
    except Exception as e:
        return ToolResult(
            success=False,
            tool_name="generate_docx",
            data={},
            sources=[],
            error=f"DOCX generation failed: {str(e)}",
        )


def generate_excel_stub(content: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
    """Execute Member 4 Excel spreadsheet generation."""
    try:
        from tools.output_generator import generate_outputs
        data = _get_analysis_data(content)
        output_dir = PROJECT_ROOT / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        result = generate_outputs(data, str(output_dir), formats=["xlsx"])
        excel_path = result.get("xlsx")
        val = _validate_file_output(excel_path)
        
        if not val["file_exists"] or val["size_bytes"] == 0:
             return ToolResult(
                success=False,
                tool_name="generate_excel",
                data=val,
                sources=[],
                error="Excel generation failed: File was not created or is empty.",
            )
            
        return ToolResult(
            success=True,
            tool_name="generate_excel",
            data={
                "status": "Excel generation completed successfully",
                "file_path": excel_path,
                "file_name": Path(excel_path).name if excel_path else "Approval_Note.xlsx",
                **val
            },
            sources=[excel_path] if excel_path else [],
            error=None,
        )
    except Exception as e:
        return ToolResult(
            success=False,
            tool_name="generate_excel",
            data={},
            sources=[],
            error=f"Excel generation failed: {str(e)}",
        )

