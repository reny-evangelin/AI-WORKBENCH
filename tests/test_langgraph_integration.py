import os
import sys
import warnings

# Suppress noisy dependency warnings from opentelemetry/grpc and huggingface_hub
warnings.filterwarnings("ignore", category=RuntimeWarning, module="opentelemetry")
warnings.filterwarnings("ignore", message=".*unauthenticated requests to the HF Hub.*")

from agent.graph.workflow import process_request

def test_langgraph_pipeline():
    """Test the full LangGraph + Ollama pipeline locally."""
    request_text = "What is the purpose of a pump in a process plant?"
    response = process_request(request_text)
    
    assert response.status == "success"
    assert response.answer is not None
    assert len(response.answer) > 0
