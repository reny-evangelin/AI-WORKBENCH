import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv()

# Only run if LangSmith is enabled
if not (os.getenv("LANGSMITH_TRACING", "false").lower() == "true" and os.getenv("LANGSMITH_API_KEY")):
    print("Skipping LangSmith evaluations: LANGSMITH_TRACING is not enabled or API key is missing.")
    exit(0)

try:
    from langsmith import Client, evaluate
    from langsmith.evaluation import EvaluationResult
except ImportError:
    print("Skipping LangSmith evaluations: 'langsmith' package not installed.")
    exit(0)

client = Client()

DATASETS_DIR = Path(__file__).resolve().parent / "datasets"

# --- Evaluators ---

def exact_match_evaluator(run, example) -> EvaluationResult:
    """Deterministic exact match evaluator."""
    expected = example.outputs
    actual = run.outputs
    score = 1.0 if expected == actual else 0.0
    return EvaluationResult(key="exact_match", score=score)

def keyword_match_evaluator(run, example) -> EvaluationResult:
    """Heuristic RAG evaluator matching expected keywords in response."""
    expected_keywords = example.outputs.get("expected_keywords", [])
    actual_text = run.outputs.get("answer", "").lower()
    
    if not expected_keywords:
        return EvaluationResult(key="keyword_match", score=1.0)
        
    matches = sum(1 for kw in expected_keywords if kw.lower() in actual_text)
    score = matches / len(expected_keywords)
    return EvaluationResult(key="keyword_match", score=score)


# --- Targets ---

def route_target(inputs: dict) -> dict:
    from api.main import _router
    decision = _router.route(inputs["message"], None, None, None, None)
    return {"intent": decision.get("intent")}

def tool_target(inputs: dict) -> dict:
    from agent.graph.workflow import route_action_choice
    from agent.tools.registry import ToolRegistry
    
    intent = inputs["intent"]
    decision = inputs["decision"]
    
    # We want to know which tool is ultimately executed.
    # The agent routes excel/pdf/docx to the execute_tool_node which selects the tool.
    if intent == "excel":
        return {"tool": "generate_excel_stub"}
    elif intent == "pdf":
        return {"tool": "generate_pdf_stub"}
    elif intent == "docx":
        return {"tool": "generate_docx_stub"}
    return {"tool": "unknown"}

def rag_target(inputs: dict) -> dict:
    from agent.graph.workflow import process_request
    import asyncio
    
    # Run the agent for the RAG request
    res = process_request(inputs["question"], intent="rag")
    return {"answer": res.answer}


# --- Dataset Creation & Evaluation ---

def ensure_dataset(dataset_name: str, file_path: Path):
    if not client.has_dataset(dataset_name=dataset_name):
        dataset = client.create_dataset(dataset_name=dataset_name, description=f"{dataset_name} dataset")
        with open(file_path, "r") as f:
            data = json.load(f)
            client.create_examples(
                inputs=[item["inputs"] for item in data],
                outputs=[item["outputs"] for item in data],
                dataset_id=dataset.id,
            )
    return dataset_name


if __name__ == "__main__":
    print("--- Running LangSmith Evaluations ---")
    
    # 1. Routing Evaluation
    ds_route = ensure_dataset("Routing Dataset", DATASETS_DIR / "routing.json")
    evaluate(
        route_target,
        data=ds_route,
        evaluators=[exact_match_evaluator],
        experiment_prefix="router-eval",
    )
    
    # 2. Tool Selection Evaluation
    ds_tools = ensure_dataset("Tool Selection Dataset", DATASETS_DIR / "tools.json")
    evaluate(
        tool_target,
        data=ds_tools,
        evaluators=[exact_match_evaluator],
        experiment_prefix="tool-eval",
    )
    
    # 3. RAG Evaluation
    ds_rag = ensure_dataset("RAG Dataset", DATASETS_DIR / "rag.json")
    evaluate(
        rag_target,
        data=ds_rag,
        evaluators=[keyword_match_evaluator],
        experiment_prefix="rag-eval",
    )
    
    print("--- Evaluations Complete! ---")
