# AI Workflows - Quick Start Guide

Local, offline-capable AI system with multiple entry points.

## Features

- ✈️ **Offline by Default** - Set `OFFLINE_MODE=true` (default)
- 🦙 **Ollama Integration** - Local LLM inference
- 🔍 **Vector Search** - Chroma database for RAG
- 🐍 **Multiple Entry Points** - CLI, REST API, Python SDK, Telegram
- 🔌 **Decoupled Services** - Telegram bot runs independently
- 💾 **Persistent Data** - Docker volumes for models and embeddings
- ⚙️ **Configurable** - YAML-based models and prompts

## Quick Start (Docker Compose)

### 1. Prerequisites

- Docker and Docker Compose installed
- 4GB+ RAM available
- Internet connection for initial setup (model downloads)

### 2. Setup

```bash
# Navigate to ai-workflows directory
cd ai-workflows

# Copy environment template
cp .env.example .env

# (Optional) Edit .env to customize settings
# Default: OFFLINE_MODE=true
```

### 3. Start Services

```bash
# Start all services (Ollama, API, optional Telegram bot)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 4. Test API Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "offline_mode": true,
  "ollama_available": true,
  "config": {...}
}
```

### 5. Try a Query

```bash
# Add sample documents
curl -X POST http://localhost:8000/documents/add \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Python is a programming language",
      "Docker is a containerization platform"
    ],
    "collection": "documents"
  }'

# Run RAG query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Python?",
    "n_results": 5
  }'
```

## Entry Points

### REST API

Base URL: `http://localhost:8000`

**Endpoints:**
- `GET /health` - Health check
- `GET /config` - Get configuration
- `POST /documents/add` - Add documents to vector DB
- `POST /query` - Run RAG query
- `POST /generate` - Generate text (no RAG)

### Python SDK

```python
from src.api.sdk import AIWorkflows

ai = AIWorkflows()

# Add documents
ai.add_documents([
    "Document 1 text",
    "Document 2 text",
])

# Query with RAG
response = ai.query("What is in the documents?")
print(response)

# Direct generation
response = ai.generate("Explain Python")
print(response)
```

### CLI

```bash
# Query
python -m src.api.cli query "What is Python?"

# Generate (no RAG)
python -m src.api.cli generate "Explain machine learning"

# Add documents from JSON file
python -m src.api.cli add-documents --file docs.json

# Check health
python -m src.api.cli health
```

**JSON format for `docs.json`:**
```json
{
  "texts": [
    "Document 1",
    "Document 2"
  ],
  "ids": ["doc1", "doc2"]
}
```

### Telegram Bot

1. Create bot with [@BotFather](https://t.me/BotFather)
2. Set token in `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   ```
3. Start Telegram bot service:
   ```bash
   docker-compose up telegram-bot
   ```
4. Message the bot on Telegram

## Configuration

### Offline Mode (Airplane Mode)

```bash
# Default: offline (no internet access)
OFFLINE_MODE=true

# Enable internet (for external API calls, model downloads)
OFFLINE_MODE=false
```

### Models

Edit `config/models.yaml`:
```yaml
models:
  embedding:
    name: "BAAI/bge-small-en-v1.5"
  llm:
    name: "mistral"  # or: neural-chat, orca-mini, llama2
```

### Prompts

Edit `config/prompts.yaml` to customize system prompts.

## Troubleshooting

### Ollama not available

```bash
# Check Ollama service logs
docker-compose logs ollama

# Restart Ollama
docker-compose restart ollama

# Check if models are downloaded
curl http://localhost:11434/api/tags
```

### API service fails to start

```bash
# Check logs
docker-compose logs app

# Verify health of Ollama first
docker-compose logs ollama

# Restart app
docker-compose restart app
```

### Telegram bot not responding

```bash
# Check if token is set
docker-compose logs telegram-bot

# Verify REST API is accessible
curl http://localhost:8000/health

# Restart bot
docker-compose restart telegram-bot
```

### High memory usage

- Reduce Ollama model size (use `orca-mini` instead of `mistral`)
- Reduce `n_results` in queries
- Clear Chroma database: `docker volume rm ai-workflows_chroma_data`

## Data Persistence

- **Ollama models**: Docker volume `ollama_models`
- **Chroma embeddings**: Docker volume `chroma_data`
- **Configuration**: Mounted read-only from `./config/`

Models and embeddings persist across:
- Container restarts
- Container rebuilds
- Service upgrades

## Development

### Running Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Download models (first run only)
ollama pull mistral
ollama serve &

# Run REST API
python -m src.api.rest_api

# In another terminal, run CLI
python -m src.api.cli query "Test query"
```

### Adding Custom Workflows

Create workflow file in `src/workflows/`:

```python
# src/workflows/custom.py
from ..rag import RAGPipeline
from ..models import OllamaModel
from ..embeddings import ChromaVectorDB
from ..config import config

class CustomWorkflow:
    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.vector_db = ChromaVectorDB(db_path=str(config.chroma_db_dir))
        self.model = OllamaModel()
        self.rag = RAGPipeline(self.vector_db, self.model)
    
    def run(self, input_data):
        # Your custom logic here
        pass
```

## API Development

Add new endpoints to `src/api/rest_api.py`:

```python
@app.post("/custom-endpoint")
async def custom_endpoint(data: YourInputModel):
    # Your logic
    return {"result": ...}
```

## Environment Variables

See `.env.example` for all available variables:

- `OFFLINE_MODE` - Enable/disable internet access (default: true)
- `OLLAMA_HOST` - Ollama service URL
- `OLLAMA_MODEL` - LLM model to use
- `API_HOST` - API server host
- `API_PORT` - API server port
- `TELEGRAM_BOT_TOKEN` - Telegram bot token (optional)
- `TELEGRAM_API_URL` - API URL for bot to call

## Maintenance

### Disk Space Management

Docker build cache can accumulate over time. Clean it up regularly:

```bash
# Remove all unused build cache
docker builder prune -af

# Remove dangling images
docker image prune -af

# Full system cleanup (removes unused volumes/networks too)
docker system prune -af
```

**Estimated disk usage:**
- Docker images: ~10GB (Ollama + ai-workflows)
- Volumes (persistent data): ~4-5GB (Ollama models + Chroma vectors)
- **Total: ~14-15GB** (intentional - models persist across restarts)

**Recommendation:** Run `docker builder prune -af` monthly to prevent build cache from consuming excessive disk space.

## License

See LICENSE file for details.
