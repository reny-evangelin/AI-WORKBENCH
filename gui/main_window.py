import sys
import os
import platform
import subprocess
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QTextBrowser, QPushButton, QLabel, QScrollArea, QFrame,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor

from gui.styles import MAIN_STYLESHEET
from gui.chat_thread import ChatThread
from services.ollama_service import OllamaMonitor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Engineering Assistant")
        self.resize(1000, 700)
        self.setStyleSheet(MAIN_STYLESHEET)
        
        self.history = []
        self.chat_thread = None

        self._init_ui()
        self._init_services()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        title_label = QLabel("AI Workbench")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        sidebar_layout.addWidget(title_label)
        
        new_chat_btn = QPushButton("New Chat")
        new_chat_btn.setObjectName("primary_button")
        new_chat_btn.clicked.connect(self.clear_chat)
        sidebar_layout.addWidget(new_chat_btn)
        
        output_label = QLabel("Generated Reports")
        output_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px; margin-bottom: 10px;")
        sidebar_layout.addWidget(output_label)
        
        self.output_list = QListWidget()
        self.output_list.setStyleSheet("background-color: #2d2d35; border: 1px solid #3a3a44; border-radius: 4px; padding: 5px;")
        self.output_list.itemDoubleClicked.connect(self._open_output_file)
        sidebar_layout.addWidget(self.output_list)
        
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self._refresh_output_list)
        sidebar_layout.addWidget(refresh_btn)
        
        sidebar_layout.addStretch()
        
        main_layout.addWidget(self.sidebar)

        # --- Middle Border ---
        left_border = QFrame()
        left_border.setObjectName("left_border")
        left_border.setFixedWidth(1)
        main_layout.addWidget(left_border)

        # --- Main Chat Area ---
        chat_area_widget = QWidget()
        chat_layout = QVBoxLayout(chat_area_widget)
        chat_layout.setContentsMargins(20, 20, 20, 20)

        # Scroll Area for Chat
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setObjectName("chat_scroll_area")
        self.chat_scroll.setWidgetResizable(True)
        
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setReadOnly(True)
        self.chat_display.setObjectName("chat_scroll_widget")
        self.chat_scroll.setWidget(self.chat_display)
        
        chat_layout.addWidget(self.chat_scroll)

        # Input Area
        input_layout = QHBoxLayout()
        self.chat_input = QTextEdit()
        self.chat_input.setObjectName("chat_input")
        self.chat_input.setFixedHeight(80)
        self.chat_input.setPlaceholderText("Type your message here... (Shift+Enter for new line)")
        
        # Override keyPressEvent to handle Enter without Shift
        self.chat_input.keyPressEvent = self._handle_input_keypress

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("primary_button")
        self.send_btn.setFixedHeight(80)
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_btn)

        chat_layout.addLayout(input_layout)
        main_layout.addWidget(chat_area_widget)

        # --- Right Border ---
        right_border = QFrame()
        right_border.setObjectName("right_border")
        right_border.setFixedWidth(1)
        main_layout.addWidget(right_border)

        # --- Activity Panel ---
        self.activity_panel = QFrame()
        self.activity_panel.setObjectName("activity_panel")
        self.activity_panel.setFixedWidth(250)
        activity_layout = QVBoxLayout(self.activity_panel)
        
        activity_title = QLabel("System Status")
        activity_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        activity_layout.addWidget(activity_title)
        
        self.ollama_status_label = QLabel("Ollama: Checking...")
        self.model_status_label = QLabel("Model: Checking...")
        
        activity_layout.addWidget(self.ollama_status_label)
        activity_layout.addWidget(self.model_status_label)
        activity_layout.addStretch()

        main_layout.addWidget(self.activity_panel)

        self._append_system_message("Welcome to the AI Engineering Assistant GUI! How can I help you today?")
        
        self._refresh_output_list()

    def _init_services(self):
        self.monitor = OllamaMonitor(self)
        self.monitor.status_changed.connect(self._update_status)
        self.monitor.start()

    def _update_status(self, is_reachable, is_model_avail, model_name, host):
        if is_reachable:
            self.ollama_status_label.setText(f"Ollama: Reachable ({host})")
            self.ollama_status_label.setStyleSheet("color: #00b894;")
        else:
            self.ollama_status_label.setText("Ollama: Unreachable")
            self.ollama_status_label.setStyleSheet("color: #ff7675;")

        if is_model_avail:
            self.model_status_label.setText(f"Model: {model_name} (Available)")
            self.model_status_label.setStyleSheet("color: #00b894;")
        else:
            self.model_status_label.setText(f"Model: {model_name} (Not Found)")
            self.model_status_label.setStyleSheet("color: #ff7675;")

    def _handle_input_keypress(self, event):
        if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
            self.send_message()
            event.accept()
        else:
            QTextEdit.keyPressEvent(self.chat_input, event)

    def send_message(self):
        text = self.chat_input.toPlainText().strip()
        if not text:
            return

        self._append_user_message(text)
        self.chat_input.clear()
        
        # Disable input while processing
        self.chat_input.setDisabled(True)
        self.send_btn.setDisabled(True)

        self.chat_thread = ChatThread(text, list(self.history), self)
        self.chat_thread.response_ready.connect(self._on_agent_response)
        self.chat_thread.error_occurred.connect(self._on_agent_error)
        self.chat_thread.start()

    def _on_agent_response(self, status, text, sources):
        self.chat_input.setDisabled(False)
        self.send_btn.setDisabled(False)
        self.chat_input.setFocus()
        
        self._append_agent_message(text, sources)
        
        # Update history
        # We need to grab the last user input which is at the end of the history?
        # Actually we didn't add it to history yet. Let's rebuild history here.
        # Wait, the history is passed to agent but we need to track it manually.
        user_text = self.chat_thread.user_input
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": text})
        if len(self.history) > 10:
            self.history = self.history[-10:]

    def _on_agent_error(self, error_msg):
        self.chat_input.setDisabled(False)
        self.send_btn.setDisabled(False)
        self.chat_input.setFocus()
        self._append_system_message(f"Error: {error_msg}")

    def clear_chat(self):
        self.history.clear()
        self.chat_display.clear()
        self._append_system_message("Chat history cleared. Started a new session.")

    def _append_user_message(self, text):
        self.chat_display.append(f"<b style='color: #6c5ce7;'>You:</b><br>{text}<br>")
        self._scroll_to_bottom()

    def _append_agent_message(self, text, sources):
        import json
        import urllib.parse
        from pathlib import Path
        
        try:
            data = json.loads(text)
            if data.get("type") == "file":
                doc_type = data.get("file_type", "document").title()
                filename = data.get("filename", "")
                path = data.get("path", "")
                path_uri = Path(path).as_uri()
                
                msg = f"<b style='color: #00b894;'>AI:</b><br>"
                msg += f"✓ {doc_type} generated successfully<br><br>"
                msg += f"<b>{filename}</b><br><br>"
                msg += f"<a href='{path_uri}' style='color: #74b9ff;'>[Open Document]</a><br>"
                
                # Refresh output list
                self._refresh_output_list()
            else:
                raise ValueError("Not a file JSON object")
        except:
            formatted = text.replace('\n', '<br>')
            msg = f"<b style='color: #00b894;'>AI:</b><br>{formatted}<br>"
            
        if sources:
            sources_text = ", ".join(sources)
            msg += f"<small style='color: #a0a0ab;'><i>Sources: {sources_text}</i></small><br>"
        msg += "<br>"
        self.chat_display.append(msg)
        self._scroll_to_bottom()

    def _append_system_message(self, text):
        self.chat_display.append(f"<i style='color: #fdcb6e;'>{text}</i><br><br>")
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        # Allow UI to update, then scroll
        QTimer.singleShot(10, lambda: self.chat_display.moveCursor(QTextCursor.End))

    def _refresh_output_list(self):
        self.output_list.clear()
        # Find the path to the outputs directory relative to this script (d:\AI-WORKBENCH\gui\main_window.py)
        outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
        if os.path.exists(outputs_dir):
            for file in os.listdir(outputs_dir):
                if file.endswith((".pdf", ".docx", ".xlsx")):
                    item = QListWidgetItem(file)
                    self.output_list.addItem(item)

    def _open_output_file(self, item):
        file_name = item.text()
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", file_name)
        if os.path.exists(file_path):
            if platform.system() == 'Darwin':       # macOS
                subprocess.call(('open', file_path))
            elif platform.system() == 'Windows':    # Windows
                os.startfile(file_path)
            else:                                   # linux variants
                subprocess.call(('xdg-open', file_path))

    def closeEvent(self, event):
        if self.monitor:
            self.monitor.stop()
        super().closeEvent(event)
