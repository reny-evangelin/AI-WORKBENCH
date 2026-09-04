"""
config.py — Configuration Management for Member 2 Agent
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()


class Settings:
    """Agent configuration loaded from environment variables with safe defaults."""

    def __init__(self):
        self.ollama_base_url: str = os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        ).rstrip("/")
        self.ollama_model: str = os.getenv(
            "OLLAMA_MODEL", "qwen2.5-coder:1.5b"
        )
        self.temperature: float = float(os.getenv("TEMPERATURE", "0.0"))
        self.request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "120"))

    def as_dict(self) -> dict:
        return {
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "temperature": self.temperature,
            "request_timeout": self.request_timeout,
        }


# Global singleton instance
settings = Settings()
