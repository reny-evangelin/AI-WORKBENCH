@echo off
echo Starting Ollama...
start "Ollama" ollama serve

echo Starting FastAPI Backend...
start "FastAPI Backend" cmd /c "call .venv\Scripts\activate && python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Vite Frontend...
start "Vite Frontend" cmd /c "cd frontend && npm run dev"

echo All services started!
