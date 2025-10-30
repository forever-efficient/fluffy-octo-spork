"""
AI Workflows - Local, offline-capable AI system with multiple entry points.

Features:
- Completely offline by default (OFFLINE_MODE environment variable)
- Multiple entry points: CLI, REST API, Python SDK, Telegram bot
- Vector database with Chroma (local, persistent)
- LLM inference via Ollama
- Configuration-driven workflows and prompts
- Idempotent data operations
"""

__version__ = "0.1.0"
