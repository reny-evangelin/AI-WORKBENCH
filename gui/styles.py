# gui/styles.py
# Modern AI Workbench Dark Theme

COLORS = {
    "bg_main": "#1e1e24",
    "bg_panel": "#25252d",
    "bg_card": "#2d2d35",
    "text_primary": "#e1e1e6",
    "text_secondary": "#a0a0ab",
    "accent": "#6c5ce7",
    "accent_hover": "#8174e9",
    "success": "#00b894",
    "warning": "#fdcb6e",
    "error": "#ff7675",
    "border": "#3a3a44",
}

MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_main']};
}}

QWidget {{
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Inter', sans-serif;
}}

/* Sidebars and Panels */
QFrame#sidebar, QFrame#activity_panel {{
    background-color: {COLORS['bg_panel']};
    border: none;
}}

/* Borders */
QFrame#left_border {{
    border-right: 1px solid {COLORS['border']};
}}
QFrame#right_border {{
    border-left: 1px solid {COLORS['border']};
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 16px;
    color: {COLORS['text_primary']};
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
}}
QPushButton:pressed {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton#primary_button {{
    background-color: {COLORS['accent']};
    border: none;
    font-weight: bold;
}}
QPushButton#primary_button:hover {{
    background-color: {COLORS['accent_hover']};
}}
QPushButton#primary_button:disabled {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_secondary']};
}}

/* Chat Input */
QTextEdit#chat_input {{
    background-color: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px;
    font-size: 14px;
}}
QTextEdit#chat_input:focus {{
    border: 1px solid {COLORS['accent']};
}}

/* ScrollBars */
QScrollBar:vertical {{
    border: none;
    background: {COLORS['bg_main']};
    width: 10px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

/* Chat Area */
QScrollArea#chat_scroll_area {{
    background-color: {COLORS['bg_main']};
    border: none;
}}
QWidget#chat_scroll_widget {{
    background-color: {COLORS['bg_main']};
}}
"""
