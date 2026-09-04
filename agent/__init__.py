"""
Member 2 — Main AI Agent Package
"""

from .config import Settings, settings
from .ollama_client import OllamaClient

__all__ = ["Settings", "settings", "OllamaClient"]
