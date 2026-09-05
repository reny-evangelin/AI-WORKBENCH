import sys
import subprocess
import shutil
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

def start_services():
    try:
        # Check if ollama is in native PATH
        ollama_path = shutil.which("ollama")
        
        if ollama_path:
            # Native Windows or Linux
            process = subprocess.Popen(
                [ollama_path, "serve"],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            return process
        elif sys.platform == "win32" and shutil.which("wsl"):
            # Fallback for Windows: Try starting it via WSL
            print("Ollama not found in Windows PATH. Attempting to start via WSL...")
            process = subprocess.Popen(
                ["wsl", "-e", "ollama", "serve"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return process
        else:
            print("Ollama executable not found in PATH or WSL. Please start it manually.")
            return None
    except Exception as e:
        print(f"Failed to start Ollama automatically: {e}")
        return None

def main():
    app = QApplication(sys.argv)
    
    # Start background systems
    ollama_process = start_services()
    
    window = MainWindow()
    window.show()
    exit_code = app.exec()
    
    # Cleanup on exit
    if ollama_process:
        ollama_process.terminate()
        
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
