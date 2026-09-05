#!/bin/bash

# Trap ctrl-c and call cleanup
trap cleanup INT

function cleanup() {
    echo ""
    echo "Stopping all services..."
    kill $(jobs -p)
    exit
}

echo "Checking Ollama..."
if ! pgrep -x "ollama" > /dev/null
then
    echo "Starting Ollama..."
    ollama serve &
else
    echo "Ollama is already running."
fi

echo "Starting FastAPI Backend..."
# Determine OS to run the right venv activate
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
fi

python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload &

echo "Starting Vite Frontend..."
cd frontend
npm run dev &
cd ..

echo ""
echo "========================================="
echo "All services started successfully!"
echo "Backend: http://127.0.0.1:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop all services."
echo "========================================="
echo ""

# Wait for background jobs
wait
