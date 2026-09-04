"""
scripts/check_ollama.py — Diagnostic Health Check for Ollama Service
"""

import sys
import os

# Add parent directory to sys.path so agent module imports cleanly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.config import settings
from agent.ollama_client import OllamaClient


def run_health_check() -> bool:
    print("=======================================================")
    print("  SIH117 -- Member 2: Ollama Service Health Check")
    print("=======================================================")

    client = OllamaClient(settings)
    url = settings.ollama_base_url
    model = settings.ollama_model

    print(f"\n[1/4] Checking Ollama endpoint ({url}) ...")
    if not client.is_reachable():
        print(f"\n[ERROR] Ollama server is not reachable at {url}.\n")
        print("Required Action:")
        print("  1. Ensure Ollama is installed and running.")
        print("  2. If using WSL, ensure service is active (`ollama serve`).")
        print("  3. Verify port 11434 is accessible.")
        return False
    print("  [OK] Ollama server reachable")

    print("\n[2/4] Checking Ollama API response ...")
    print("  [OK] Ollama API responding")

    print(f"\n[3/4] Checking model '{model}' availability ...")
    if not client.is_model_available():
        print(f"\n[ERROR] Model '{model}' not found in Ollama.\n")
        print("Required Action:")
        print(f"  Run: ollama pull {model}")
        return False
    print(f"  [OK] Model {model} available")

    print("\n[4/4] Testing sample generation ...")
    try:
        prompt = "Reply with exactly: Ollama environment is READY."
        output = client.generate_response(prompt).strip()
        print(f"  Response: {output}")
        print("  [OK] Test generation successful")
    except Exception as e:
        print(f"\n[ERROR] Test generation failed: {e}")
        return False

    print("\n=======================================================")
    print("  Ollama environment is READY.")
    print("=======================================================")
    return True


if __name__ == "__main__":
    success = run_health_check()
    sys.exit(0 if success else 1)
