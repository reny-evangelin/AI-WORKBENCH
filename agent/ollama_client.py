"""
ollama_client.py — Ollama Connection Layer for Member 2 Agent
"""
import requests
from typing import Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from .config import Settings, settings


class OllamaClient:
    """Isolates Ollama LLM interaction and connectivity checks."""

    def __init__(self, config: Optional[Settings] = None):
        self.config = config or settings
        self._llm: Optional[ChatOllama] = None

    def get_llm(self) -> ChatOllama:
        """Returns lazy-initialized ChatOllama instance."""
        if self._llm is None:
            self._llm = ChatOllama(
                model=self.config.ollama_model,
                base_url=self.config.ollama_base_url,
                temperature=self.config.temperature,
                timeout=self.config.request_timeout,
            )
        return self._llm

    def is_reachable(self) -> bool:
        """Check if the Ollama REST API endpoint is responding."""
        try:
            res = requests.get(f"{self.config.ollama_base_url}/api/tags", timeout=5)
            return res.status_code == 200
        except Exception:
            return False

    def is_model_available(self) -> bool:
        """Check if configured model is pulled in Ollama."""
        try:
            res = requests.get(f"{self.config.ollama_base_url}/api/tags", timeout=5)
            if res.status_code != 200:
                return False
            data = res.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            target = self.config.ollama_model
            return any(target in m or m in target for m in models)
        except Exception:
            return False

    def generate_response(self, prompt: str) -> str:
        """Sends a simple text prompt and returns response string."""
        llm = self.get_llm()
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        return str(response.content)
