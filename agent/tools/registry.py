"""
registry.py — Central Tool Registry for Safe Agentic Capability Execution
"""

from typing import Dict, Callable, Any, Set
from .interfaces import (
    ToolResult,
    analyze_pid_stub,
    search_knowledge_stub,
    generate_pdf_stub,
    generate_docx_stub,
    generate_excel_stub,
)


class ToolRegistry:
    """Registry maintaining authorized tools available to the Member 2 agent."""

    def __init__(self):
        self._tools: Dict[str, Callable[..., ToolResult]] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        self.register_tool("analyze_pid", analyze_pid_stub)
        self.register_tool("search_knowledge", search_knowledge_stub)
        self.register_tool("generate_pdf", generate_pdf_stub)
        self.register_tool("generate_docx", generate_docx_stub)
        self.register_tool("generate_excel", generate_excel_stub)

    def register_tool(self, tool_name: str, tool_func: Callable[..., ToolResult]):
        """Register a new tool function under tool_name."""
        self._tools[tool_name.lower().strip()] = tool_func

    def is_registered(self, tool_name: str) -> bool:
        """Check if tool_name is registered and allowed."""
        return tool_name.lower().strip() in self._tools

    def list_tools(self) -> Set[str]:
        """Return names of all registered tools."""
        return set(self._tools.keys())

    def execute_tool(self, tool_name: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Safely execute registered tool. Rejects unauthorized tool execution."""
        name = tool_name.lower().strip()
        if not self.is_registered(name):
            return ToolResult(
                success=False,
                tool_name=tool_name,
                data={},
                sources=[],
                error=f"Unauthorized tool execution requested: '{tool_name}'. Only registered tools may execute.",
            )

        try:
            tool_func = self._tools[name]
            return tool_func(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                data={},
                sources=[],
                error=f"Error executing tool '{tool_name}': {str(e)}",
            )


# Global tool registry singleton
tool_registry = ToolRegistry()
