#!/bin/bash
# Ollama entrypoint - pulls model on first run, then serves

set -e

MODEL=${OLLAMA_MODEL:-mistral}
MODELS_DIR="/root/.ollama/models"
INIT_FLAG="$MODELS_DIR/.initialized_${MODEL}"

echo "Starting Ollama server..."
/bin/ollama serve &
SERVER_PID=$!

# Wait for server to be ready (max 60 seconds)
echo "Waiting for Ollama server to respond..."
for i in {1..60}; do
  if /bin/ollama list &>/dev/null; then
    echo "✓ Ollama server is ready"
    break
  fi
  sleep 1
done

# Check if this specific model needs to be pulled
if [ ! -f "$INIT_FLAG" ]; then
  echo "Pulling model: $MODEL (this may take a few minutes)..."
  if /bin/ollama pull "$MODEL"; then
    mkdir -p "$MODELS_DIR"
    touch "$INIT_FLAG"
    echo "✓ Model pull successful: $MODEL"
  else
    echo "✗ Model pull failed: $MODEL"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
  fi
else
  echo "✓ Model already available: $MODEL"
fi

echo "✓ Ollama ready with model: $MODEL"
echo "Server running on 0.0.0.0:11434"

# Keep server running in foreground
wait $SERVER_PID