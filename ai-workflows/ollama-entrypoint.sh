#!/bin/bash
# Ollama entrypoint - pulls model on first run, then serves normally

MODEL=${OLLAMA_MODEL:-mistral}
MODELS_DIR="/root/.ollama/models"
INIT_FLAG="$MODELS_DIR/.initialized"

# Start Ollama server
/bin/ollama serve &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for Ollama server to start..."
for i in {1..60}; do
  if /bin/ollama list &>/dev/null; then
    echo "Ollama server is ready"
    break
  fi
  if [ $i -eq 60 ]; then
    echo "Timeout waiting for Ollama server"
    kill $SERVER_PID
    exit 1
  fi
  sleep 1
done

# Check if model needs to be pulled
if [ ! -f "$INIT_FLAG" ]; then
  echo "First run detected - pulling model: $MODEL"
  /bin/ollama pull $MODEL
  if [ $? -eq 0 ]; then
    touch "$INIT_FLAG"
    echo "Model $MODEL pulled successfully"
  else
    echo "Failed to pull model $MODEL"
    kill $SERVER_PID
    exit 1
  fi
else
  echo "Model already initialized: $MODEL"
fi

echo "Ollama ready with model: $MODEL"

# Keep server running
wait $SERVER_PID
