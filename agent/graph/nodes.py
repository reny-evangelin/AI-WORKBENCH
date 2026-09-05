"""
nodes.py — LangGraph Workflow Nodes for Member 2 Agent
"""
import json
import logging
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from .state import AgentState
from .router import route_request_intent
from ..chains import run_agent_request
from ..tools import tool_registry
from ..llm import get_llm

MAX_ITERATIONS = 5
logger = logging.getLogger("agent")


def validate_input(state: AgentState) -> Dict[str, Any]:
    """Node: Validates user input and rejects empty or whitespace requests early without calling LLM."""
    raw_req = state.get("user_request", "")
    clean_req = raw_req.strip() if raw_req else ""

    if not clean_req:
        return {
            "user_request": "",
            "status": "needs_input",
            "route": None,
            "response": "User request cannot be empty. Please provide a valid engineering query.",
            "sources": [],
            "messages": state.get("messages", []),
            "iteration_count": 0,
            "observations": [],
            "plan": [],
        }

    logger.info(f"[AGENT] User request received: {clean_req}")
    return {
        "user_request": clean_req,
        "status": "ready",
        "sources": state.get("sources", []),
        "messages": state.get("messages", []),
        "iteration_count": 0,
        "observations": [],
        "plan": [],
        "current_step": 0,
    }


def safe_json_parse(text: str) -> dict:
    """Helper to extract and parse JSON safely."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {}

def detect_intent(state: AgentState) -> Dict[str, Any]:
    """Node: Uses LLM to accurately detect intent, especially document generation."""
    user_req = state.get("user_request", "")
    try:
        llm = get_llm()
        prompt = PromptTemplate.from_template(
            "Analyze the following user request and classify the intent. "
            "If they are asking to generate, create, or make a document, report, or spreadsheet, the intent is 'document_generation'. "
            "Otherwise, if it's about P&ID, use 'pid'. If it's about engineering knowledge, use 'knowledge'. Otherwise 'general'.\n"
            "Also extract the document type if applicable (pdf, docx, excel).\n"
            "Return ONLY valid JSON like: {{\"intent\": \"document_generation\", \"document_type\": \"pdf\"}}\n\n"
            "User Request: {request}"
        )
        res = (prompt | llm).invoke({"request": user_req})
        parsed = safe_json_parse(res.content)
        intent = parsed.get("intent", "general")
        document_type = parsed.get("document_type", None)
        
        logger.info(f"[STATE] intent={intent} document_type={document_type}")
        return {
            "intent": intent,
            "document_type": document_type
        }
    except Exception as e:
        logger.error(f"Intent detection failed: {e}")
        # Fallback to router
        try:
            route = route_request_intent(user_req)
            intent = "document_generation" if route == "document" else route
        except Exception:
            intent = "document_generation" if any(x in user_req.lower() for x in ["pdf", "excel", "word", "spreadsheet"]) else "general"
            
        return {"intent": intent, "document_type": "pdf" if "pdf" in user_req.lower() else "docx" if "word" in user_req.lower() else "excel"}


def plan_request(state: AgentState) -> Dict[str, Any]:
    """Node: Analyzes user request and creates a structured execution plan."""
    user_req = state.get("user_request", "")
    intent = state.get("intent", "general")
    doc_type = state.get("document_type", "")
    
    if intent == "document_generation":
        try:
            llm = get_llm()
            if doc_type == "excel":
                prompt_text = (
                    "Create a structured plan for generating an Excel workbook based on the user request. "
                    "Include a 'goal', an array of 'sheets' (where each sheet has a 'name' and an array of 'columns'), "
                    "and 'output_format' (excel). Ensure that if the user asks for comments or recommendations, they are explicitly included as columns or sheets.\n"
                    "Return ONLY valid JSON.\n\n"
                    "User Request: {request}"
                )
            else:
                prompt_text = (
                    "Create a structured plan for generating a document based on the user request. "
                    "Include a 'goal', an array of 'sections' (e.g. Introduction, Comments, Recommendations, Conclusion), "
                    "and 'output_format'. Ensure that if the user asks for comments or recommendations, they are explicitly in the sections array.\n"
                    "Return ONLY valid JSON.\n\n"
                    "User Request: {request}"
                )
            prompt = PromptTemplate.from_template(prompt_text)
            res = (prompt | llm).invoke({"request": user_req})
            content_text = res.content
            if "```json" in content_text:
                content_text = content_text.split("```json")[1].split("```")[0].strip()
            elif "```" in content_text:
                content_text = content_text.split("```")[1].strip()
            
            plan_data = json.loads(content_text)
            
            # Map doc_type to action
            action = f"generate_{doc_type}" if doc_type in ["pdf", "docx", "excel"] else "generate_pdf"
            
            plan = [{"step": 1, "action": action, "purpose": plan_data.get("goal", "Generate document")}]
            if doc_type == "excel":
                plan[0]["sheets"] = plan_data.get("sheets", [])
            else:
                plan[0]["sections"] = plan_data.get("sections", [])
                
            logger.info("[AGENT] Planning complete")
            return {"plan": plan, "current_step": 1}
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            action = f"generate_{doc_type}" if doc_type in ["pdf", "docx", "excel"] else "generate_pdf"
            return {"plan": [{"step": 1, "action": action, "purpose": "Generate report"}], "current_step": 1}

    # Detect multi-step intent (e.g. P&ID + Excel generation)
    lower = user_req.lower()
    if ("p&id" in lower or "pid" in lower) and ("excel" in lower or "report" in lower):
        plan = [
            {"step": 1, "action": "analyze_pid", "purpose": "Analyze P&ID drawing and extract components"},
            {"step": 2, "action": "generate_excel", "purpose": "Generate Excel report from extracted components"},
        ]
    elif intent == "pid":
        plan = [
            {"step": 1, "action": "analyze_pid", "purpose": "Analyze P&ID drawing"},
            {"step": 2, "action": "respond", "purpose": "Summarize analysis results"}
        ]
    elif intent == "knowledge":
        plan = [
            {"step": 1, "action": "search_knowledge", "purpose": "Search engineering knowledge base"},
            {"step": 2, "action": "respond", "purpose": "Answer based on search results"}
        ]
    else:
        plan = [{"step": 1, "action": "respond", "purpose": "Generate direct conversational/technical LLM answer"}]

    return {
        "plan": plan,
        "current_step": 1,
    }


def generate_content(state: AgentState) -> Dict[str, Any]:
    """Node: Generates the structured document content before passing it to the tool."""
    intent = state.get("intent", "general")
    plan = state.get("plan", [])
    if intent != "document_generation" or not plan:
        return {"generated_content": None}

    try:
        doc_type = state.get("document_type", "")
        llm = get_llm()
        
        if doc_type == "excel":
            sheets_needed = plan[0].get("sheets", [{"name": "Sheet1", "columns": ["Column1", "Column2"]}])
            prompt_text = (
                "Generate detailed content for an Excel workbook based on the user request. "
                "You MUST create the following sheets and columns: {structure}. "
                "Return ONLY a valid JSON object matching this schema:\n"
                "{{\n"
                "  \"title\": \"Workbook Title\",\n"
                "  \"sheets\": [\n"
                "    {{\n"
                "      \"name\": \"Sheet Name\",\n"
                "      \"columns\": [\"Col1\", \"Col2\"],\n"
                "      \"rows\": [\n"
                "        [\"Val1\", \"Val2\"]\n"
                "      ]\n"
                "    }}\n"
                "  ]\n"
                "}}\n"
                "User Request: {request}"
            )
            structure_json = json.dumps(sheets_needed)
        else:
            sections_needed = plan[0].get("sections", ["Introduction", "Main Content", "Conclusion"])
            prompt_text = (
                "Generate detailed content for an engineering report based on the user request. "
                "You MUST create the following sections: {structure}. "
                "Return ONLY a valid JSON object matching this schema:\n"
                "{{\n"
                "  \"title\": \"Document Title\",\n"
                "  \"sections\": [\n"
                "    {{\"heading\": \"Section Name\", \"content\": \"Detailed paragraph content\"}}\n"
                "  ]\n"
                "}}\n"
                "User Request: {request}"
            )
            structure_json = json.dumps(sections_needed)

        prompt = PromptTemplate.from_template(prompt_text)
        res = (prompt | llm).invoke({"request": state.get("user_request", ""), "structure": structure_json})
        content_text = res.content
        if "```json" in content_text:
            content_text = content_text.split("```json")[1].split("```")[0].strip()
        elif "```" in content_text:
            content_text = content_text.split("```")[1].strip()
            
        generated_content = json.loads(content_text)
        logger.info("[AGENT] Content generation successful")
        return {"generated_content": generated_content}
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        return {"generated_content": {"title": "Error Report", "sections": [{"heading": "Error", "content": "Failed to generate structured content."}]}}


def select_action(state: AgentState) -> Dict[str, Any]:
    """Node: Selects immediate operational action from the structured plan."""
    plan = state.get("plan", [])
    step_idx = state.get("current_step", 1) - 1

    if 0 <= step_idx < len(plan):
        action = plan[step_idx].get("action", "respond")
    else:
        action = "respond"

    if action == "respond":
        return {"tool_name": None, "tool_required": False}

    logger.info(f"[AGENT] Tool selected: {action}")
    
    # Use generated content if available, else blank dict
    tool_input = {"file_path": None, "query": state.get("user_request", "")}
    if action in ["generate_pdf", "generate_docx", "generate_excel"] and state.get("generated_content"):
        tool_input["content"] = state.get("generated_content")

    return {
        "tool_name": action,
        "tool_required": True,
        "tool_input": tool_input,
    }


def execute_tool_node(state: AgentState) -> Dict[str, Any]:
    """Node: Safely executes registered tool from ToolRegistry."""
    tool_name = state.get("tool_name") or ""
    tool_input = state.get("tool_input") or {}

    logger.info(f"[TOOL] {tool_name} started")

    # Check for missing inputs before executing tool
    if tool_name == "analyze_pid" and not tool_input.get("file_path"):
        obs = {
            "success": False,
            "tool_name": tool_name,
            "data": {},
            "sources": [],
            "error": "Missing required P&ID file path. Please provide the P&ID file.",
        }
    else:
        result = tool_registry.execute_tool(tool_name, tool_input)
        obs = result.model_dump()
        
    logger.info(f"[TOOL] {tool_name} completed, success: {obs.get('success')}")

    observations = list(state.get("observations", []))
    observations.append(obs)

    sources = list(state.get("sources", []))
    for src in obs.get("sources", []):
        if src not in sources:
            sources.append(src)

    return {
        "tool_result": obs,
        "observations": observations,
        "sources": sources,
    }


def evaluate_result(state: AgentState) -> Dict[str, Any]:
    """Node: Evaluates tool execution results and updates iteration counter / step progress."""
    count = state.get("iteration_count", 0) + 1
    if count >= MAX_ITERATIONS:
        return {
            "iteration_count": count,
            "status": "error",
            "response": "Execution stopped: maximum iteration limit (5) reached.",
        }

    plan = state.get("plan", [])
    current_step = state.get("current_step", 1)
    tool_res = state.get("tool_result", {})

    validation_result = None
    if tool_res and tool_res.get("success", False) and tool_res.get("tool_name") in ["generate_pdf", "generate_docx", "generate_excel"]:
        data = tool_res.get("data", {})
        if not data.get("file_exists") or data.get("size_bytes", 0) == 0:
            logger.error("[VALIDATION] File missing or empty!")
            error_msg = tool_res.get("error") or "Generated file does not exist or is empty."
            return {
                "iteration_count": count,
                "status": "error",
                "response": f"Tool execution failed during validation. {error_msg}",
            }
        else:
            logger.info(f"[VALIDATION] exists={data.get('file_exists')} size={data.get('size_bytes')}")
            validation_result = {"valid": True, "file_path": data.get("file_path")}

    if tool_res and not tool_res.get("success", False):
        error_msg = tool_res.get("error", "Tool execution failed.")
        logger.error(f"[AGENT] Tool execution failed: {error_msg}")
        return {
            "iteration_count": count,
            "status": "needs_input" if "Missing" in error_msg else "error",
            "response": error_msg,
        }

    next_step = current_step + 1
    if next_step > len(plan):
        # All planned steps completed
        return {
            "iteration_count": count,
            "status": "ready_to_finalize",
            "validation_result": validation_result
        }

    return {
        "iteration_count": count,
        "current_step": next_step,
        "status": "in_progress",
    }


def general_response(state: AgentState) -> Dict[str, Any]:
    """Node: Delegates general conversational and technical queries to LCEL pipeline."""
    user_req = state.get("user_request", "")
    history = state.get("messages", [])
    obs = state.get("observations", [])

    prompt = user_req
    if obs:
        context_str = "\n\n".join([str(o.get("data", {})) for o in obs if o.get("success")])
        if context_str:
            prompt = f"Use the following context from your tools to answer the user's question.\n\nContext Information:\n{context_str}\n\nUser Question:\n{user_req}"

    res = run_agent_request(prompt, conversation_history=history)

    updated_messages = list(history)
    updated_messages.append({"role": "user", "content": user_req})
    updated_messages.append({"role": "assistant", "content": res.answer})

    return {
        "response": res.answer,
        "status": res.status,
        "sources": state.get("sources", []) + res.sources,
        "messages": updated_messages,
    }


def finalize_agent_response(state: AgentState) -> Dict[str, Any]:
    """Node: Normalizes final output state and formats multi-step tool observation summaries."""
    if state.get("response") and state.get("status") in ["error", "needs_input"]:
        return {
            "response": state["response"],
            "status": state.get("status"),
            "sources": state.get("sources", []),
        }

    if state.get("response"):
        return {
            "response": state["response"],
            "status": state.get("status") or "success",
            "sources": state.get("sources", []),
        }

    obs_list = state.get("observations", [])
    if obs_list:
        summaries = []
        for obs in obs_list:
            t_name = obs.get("tool_name", "tool")
            if obs.get("success"):
                if t_name in ["generate_pdf", "generate_docx", "generate_excel"]:
                    file_path = obs.get("data", {}).get("file_path", "")
                    file_name = obs.get("data", {}).get("file_name", "")
                    
                    doc_type_map = {"generate_pdf": "pdf", "generate_docx": "docx", "generate_excel": "excel"}
                    doc_type = doc_type_map.get(t_name, "document")
                    
                    # Return structured machine-readable JSON for GUI
                    msg = json.dumps({
                        "success": True,
                        "type": "file",
                        "file_type": doc_type,
                        "filename": file_name,
                        "path": file_path
                    })
                    summaries.append(msg)
                    logger.info(f"[AGENT] Document generation successful: {file_path}")
                else:
                    d_status = obs.get("data", {}).get("status") or obs.get("data", {}).get("summary") or "completed successfully"
                    summaries.append(f"[{t_name}]: {d_status}")
            else:
                summaries.append(f"I couldn't generate the document.\n\nReason: {obs.get('error')}\n\nThe document-generation tool failed.")

        resp_text = "\n\n".join(summaries)
        status = "success" if any(o.get("success") for o in obs_list) else "error"
    else:
        resp_text = "No response generated."
        status = state.get("status") or "success"

    return {
        "response": resp_text,
        "status": status,
        "sources": state.get("sources", []),
    }
