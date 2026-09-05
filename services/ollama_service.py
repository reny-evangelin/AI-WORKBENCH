import time
from PySide6.QtCore import QThread, Signal
from agent.ollama_client import OllamaClient
from agent.config import settings

class OllamaMonitor(QThread):
    status_changed = Signal(bool, bool, str, str)  # is_reachable, is_model_available, model_name, host

    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = OllamaClient()
        self._is_running = True

    def run(self):
        while self._is_running:
            try:
                is_reachable = self.client.is_reachable()
                is_model_avail = self.client.is_model_available() if is_reachable else False
                self.status_changed.emit(
                    is_reachable, 
                    is_model_avail, 
                    settings.ollama_model, 
                    settings.ollama_base_url
                )
            except Exception:
                self.status_changed.emit(False, False, settings.ollama_model, settings.ollama_base_url)
            
            # Sleep 5 seconds before checking again
            time.sleep(5)

    def stop(self):
        self._is_running = False
        self.wait()
