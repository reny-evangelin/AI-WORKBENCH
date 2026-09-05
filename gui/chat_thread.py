from PySide6.QtCore import QThread, Signal
from agent import run_agent

class ChatThread(QThread):
    # Signals to communicate back to the main thread
    response_ready = Signal(str, str, list)  # status, text, sources
    error_occurred = Signal(str)

    def __init__(self, user_input, history, parent=None):
        super().__init__(parent)
        self.user_input = user_input
        self.history = history

    def run(self):
        try:
            response = run_agent(self.user_input, conversation_history=self.history)
            self.response_ready.emit(response.status, response.answer, response.sources or [])
        except Exception as e:
            self.error_occurred.emit(str(e))
