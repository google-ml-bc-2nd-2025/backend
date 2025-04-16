#!/bin/bash
set -e

# # Ollama 서비스 시작
# echo "Ollama starting..."
# ollama serve &
# OLLAMA_PID=$!

# # wait for Ollama service to be ready
# echo "waiting to start Ollama service..."
# max_attempts=30
# attempt=0
# while ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; do
#     attempt=$((attempt + 1))
#     if [ $attempt -ge $max_attempts ]; then
#         echo "Ollama timeout! Ollama service is not available after $max_attempts attempts."
#         exit 1
#     fi 
#     echo "waiting Ollama API... ($attempt/$max_attempts)"
#     sleep 2
# done

# echo "Ollama Ready to START!"

# # download the model if not exists
# MODEL=$(grep -oP 'MODEL="\K[^"]+' .env 2>/dev/null || echo "gemma3:4b")
# echo "Model '$MODEL' Checking..."
# if ! ollama list | grep -q "$MODEL"; then
#     echo "Model '$MODEL' downloading..."
#     ollama pull $MODEL
# else
#     echo "Model '$MODEL' already exists."
# fi

# START API Server
if [ -f "app.py" ]; then
    echo "API Server is starting..."
    exec python3 app.py
else
    # Waiting for Ollama service to be ready
    echo "Only Ollama service is running. Press Ctrl+C to stop."
    
    # Quit if Ollama service is not running
    wait $OLLAMA_PID
fi