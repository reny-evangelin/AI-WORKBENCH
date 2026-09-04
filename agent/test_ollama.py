"""
test_ollama.py - Test Local Ollama Connection
Member 2: Main AI Agent

Run this script to verify:
  1. Ollama server is reachable at localhost:11434
  2. The model (qwen2.5-coder:1.5b) is available and responds
  3. LangChain <-> Ollama integration is working

Usage:
    python agent/test_ollama.py
"""

import sys
import requests
from langchain_core.messages import HumanMessage
from llm import get_llm, OLLAMA_BASE_URL, OLLAMA_MODEL


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def print_separator(char="-", width=55):
    print(char * width)


def check_ollama_server(base_url: str) -> bool:
    """Ping the Ollama REST API to confirm the server is running."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def check_model_available(base_url: str, model: str) -> bool:
    """Check whether the required model is already pulled in Ollama."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code != 200:
            return False
        models = [m["name"] for m in response.json().get("models", [])]
        return any(model in m for m in models)
    except Exception:
        return False


# ─────────────────────────────────────────────
# Main Test
# ─────────────────────────────────────────────

def main():
    print_separator("=")
    print("  SIH117 -- Member 2: Ollama Connection Test")
    print_separator("=")

    # -- Test 1: Server reachability --
    print(f"\n[1/3] Checking Ollama server at {OLLAMA_BASE_URL} ...")
    if not check_ollama_server(OLLAMA_BASE_URL):
        print("  [FAIL] Ollama server is not reachable.")
        print("  --> Make sure Ollama is running:  ollama serve")
        sys.exit(1)
    print("  [OK] Ollama server is running.")

    # -- Test 2: Model availability --
    print(f"\n[2/3] Checking model '{OLLAMA_MODEL}' is available ...")
    if not check_model_available(OLLAMA_BASE_URL, OLLAMA_MODEL):
        print(f"  [FAIL] Model '{OLLAMA_MODEL}' not found.")
        print(f"  --> Pull it first:  ollama pull {OLLAMA_MODEL}")
        sys.exit(1)
    print(f"  [OK] Model '{OLLAMA_MODEL}' is available.")

    # -- Test 3: LangChain invoke --
    print(f"\n[3/3] Sending a test message via LangChain --> Ollama ...")
    print_separator()

    try:
        llm = get_llm()
        test_prompt = (
            "You are an engineering assistant. "
            "Reply in one short sentence: what is a P&ID diagram?"
        )
        messages = [HumanMessage(content=test_prompt)]
        response = llm.invoke(messages)

        print(f"  Prompt  : {test_prompt}")
        print_separator()
        print(f"  Response: {response.content}")
        print_separator()
        print("  [OK] LangChain <-> Ollama integration is working.\n")

    except Exception as e:
        print(f"  [FAIL] Error during LLM call: {e}")
        sys.exit(1)

    # -- Summary --
    print_separator("=")
    print("  ALL TESTS PASSED")
    print(f"  Model   : {OLLAMA_MODEL}")
    print(f"  Server  : {OLLAMA_BASE_URL}")
    print("  Status  : Ready for agent development")
    print_separator("=")


if __name__ == "__main__":
    main()
