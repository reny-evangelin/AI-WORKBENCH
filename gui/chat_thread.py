from PySide6.QtCore import QThread, Signal
from langchain_core.callbacks import BaseCallbackHandler
from agent import process_request
from agent.schemas import AgentResponse

class UISignalingCallback(BaseCallbackHandler):
    """Callback handler to pipe LangChain stream tokens into PySide6 Signals."""
    def __init__(self, token_signal):
        self.token_signal = token_signal
        self.stream_active = False
        
    def on_chat_model_start(self, serialized, messages, **kwargs):
        tags = kwargs.get("tags", [])
        self.stream_active = "stream_answer" in tags
        
    def on_llm_new_token(self, token: str, **kwargs):
        if self.stream_active:
            self.token_signal.emit(token)

class ChatThread(QThread):
    # Signals to communicate back to the main thread
    token_ready = Signal(str)               # token
    response_ready = Signal(str, str, list)  # status, text, sources
    error_occurred = Signal(str)

    def __init__(self, user_input, history, image_path=None, parent=None):
        super().__init__(parent)
        self.user_input = user_input
        self.history = history
        self.image_path = image_path

    def run(self):
        try:
            cb = UISignalingCallback(self.token_ready)
            response = process_request(self.user_input, image_path=self.image_path, callbacks=[cb], conversation_history=self.history)
            self.response_ready.emit(response.status, response.answer, response.sources or [])
        except Exception as e:
            self.error_occurred.emit(str(e))
