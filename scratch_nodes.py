"""
nodes.py — LangGraph Workflow Nodes for Member 2 Agent
"""
import json
import logging
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from agent.graph.state import AgentState
from agent.chains import run_agent_request
from agent.tools import tool_registry
from agent.llm import get_llm
from utils.performance import track_performance

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
    import re
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].strip()
        
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*\]', ']', text)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    raise ValueError("Invalid JSON output")


@track_performance("llm_time")
def understand_request(state: AgentState) -> Dict[str, Any]:
    """Node: Uses LLM to understand intent and generate structured payload simultaneously."""
    user_req = state.get("user_request", "")
    llm = get_llm()
    
    prompt_text = (
        "You are the central brain of an AI Engineering Assistant.\n"
        "Analyze the user request and determine the exact intent: 'chat', 'rag', 'excel', 'pdf', or 'docx'.\n\n"
        "RULES:\n"
        "- IF simple greeting/chat: intent = 'chat' AND provide 'direct_response'.\n"
        "- IF asking about project knowledge/architecture/documents: intent = 'rag' AND provide 'search_query'.\n"
        "- IF asking to generate an Excel report: intent = 'excel' AND provide 'excel_plan'. "
        "For excel_plan, preserve user data, create 'filename', 'title', and 'sheets' (with 'name', 'columns', 'rows', 'formulas').\n"
        "- IF asking to generate PDF/DOCX: intent = 'pdf' or 'docx' AND provide 'document_plan'. "
        "For document_plan, provide 'title' and 'sections' (with 'heading' and 'content').\n\n"
        "OUTPUT FORMAT: You MUST return ONLY a valid JSON object matching the 'BrainDecision' schema.\n\n"
        "User Request: {request}"
    )
    
    error_msg = ""
    decision_data = {}
    
    for attempt in range(3):
        try:
            current_prompt = prompt_text
            if error_msg:
                current_prompt += f"\n\nYOUR PREVIOUS OUTPUT FAILED WITH ERROR:\n{error_msg}\nYOU MUST FIX THE JSON SYNTAX ERROR AND RETURN ONLY VALID JSON!"
                
            prompt = PromptTemplate.from_template(current_prompt)
            res = (prompt | llm).invoke({"request": user_req})
            
            decision_data = safe_json_parse(res.content)
            
            # Validate schema
            from agent.schemas import BrainDecision
            validated = BrainDecision(**decision_data)
            
            logger.info(f"[AGENT] Intent detected: {validated.intent}")
            return {
                "intent": validated.intent,
                "brain_decision": validated.model_dump(),
            }
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Understand request failed on attempt {attempt+1}: {e}")
            
    # Fallback to simple chat error if JSON fails 3 times
    return {
        "intent": "error",
        "brain_decision": {
            "intent": "error",
            "direct_response": f"I encountered an internal error trying to plan this action: {error_msg}"
        }
    }


@track_performance("tool_routing_time")
def route_action(state: AgentState) -> Dict[str, Any]:
    """Node: Selects immediate operational action from the BrainDecision."""
    decision = state.get("brain_decision", {})
    intent = decision.get("intent", "error")

    if intent in ["excel", "pdf", "docx"]:
        content_key = f"{intent}_plan" if intent == "excel" else "document_plan"
        content = decision.get(content_key)
        
        return {
            "tool_name": f"generate_{intent}",
            "tool_required": True,
            "tool_input": {"content": content, "query": state.get("user_request", "")},
        }
    elif intent == "rag":
        return {
            "tool_name": "search_knowledge",
            "tool_required": True,
            "tool_input": {"query": decision.get("search_query", state.get("user_request", ""))},
        }
    else:
        # Chat or error
        return {
            "tool_name": None,
            "tool_required": False,
            "tool_input": {},
        }


@track_performance("tool_time")
def execute_tool_node(state: AgentState) -> Dict[str, Any]:
    """Node: Safely executes registered tool from ToolRegistry."""
    tool_name = state.get("tool_name")
    tool_input = state.get("tool_input", {})

    if not tool_name or not tool_registry.is_registered(tool_name):
        return {
            "tool_result": {
                "success": False,
                "error": f"Tool '{tool_name}' not found or unauthorized.",
            }
        }

    logger.info(f"[TOOL] {tool_name} started")

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
    """Node: Evaluates tool execution results."""
    count = state.get("iteration_count", 0) + 1
    if count >= MAX_ITERATIONS:
        return {
            "iteration_count": count,
            "status": "error",
            "response": "Execution stopped: maximum iteration limit (5) reached.",
        }

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

    return {
        "iteration_count": count,
        "status": "ready_to_finalize",
        "validation_result": validation_result
    }


@track_performance("llm_time")
def synthesize_rag(state: AgentState) -> Dict[str, Any]:
    """Node: Synthesizes final answer from RAG context."""
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
    """Node: Normalizes final output state."""
    
    # If the LLM just wanted to chat, return its direct response
    decision = state.get("brain_decision", {})
    if decision.get("intent") in ["chat", "error"] and not state.get("response"):
        resp = decision.get("direct_response") or "I couldn't process that request."
        return {
            "response": resp,
            "status": "success" if decision.get("intent") == "chat" else "error",
            "sources": []
        }

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
                summaries.append(f"I couldn't complete the task.\n\nReason: {obs.get('error')}")

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
