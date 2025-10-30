"""
Configuration management for AI Workflows.

Handles:
- OFFLINE_MODE environment variable (default: True)
- Model configuration loading (models.yaml)
- Prompt configuration loading (prompts.yaml)
- Database connection settings
- Ollama service configuration
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """Central configuration manager."""

    def __init__(self):
        """Initialize configuration from environment and config files."""
        # Offline mode (airplane mode) - default is True (offline)
        self.offline_mode = os.getenv("OFFLINE_MODE", "true").lower() in ("true", "1", "yes")
        
        # Project root (one level up from src/)
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.data_dir = self.project_root / "data"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Chroma database directory (persistent, local)
        self.chroma_db_dir = self.data_dir / "chroma_db"
        self.chroma_db_dir.mkdir(exist_ok=True)
        
        # Ollama configuration
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "mistral")
        
        # REST API configuration
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        
        # Telegram bot configuration (if using Telegram entry point)
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_api_url = os.getenv("TELEGRAM_API_URL", "http://localhost:8000")
        
        # Load configuration files
        self.models_config = self._load_yaml("models.yaml")
        self.prompts_config = self._load_yaml("prompts.yaml")
        
        # Validate offline mode constraints
        self._validate_offline_mode()
    
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        config_file = self.config_dir / filename
        if not config_file.exists():
            return {}
        
        with open(config_file, "r") as f:
            return yaml.safe_load(f) or {}
    
    def _validate_offline_mode(self) -> None:
        """Validate that offline mode constraints are met."""
        if self.offline_mode:
            # In offline mode, ensure we have local models pre-downloaded
            # This is a soft check - actual validation happens at runtime
            pass
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        return self.models_config.get("models", {}).get(model_name, {})
    
    def get_prompt_config(self, prompt_name: str) -> Dict[str, Any]:
        """Get configuration for a specific prompt."""
        return self.prompts_config.get("prompts", {}).get(prompt_name, {})
    
    def can_access_internet(self) -> bool:
        """Check if internet access is allowed."""
        return not self.offline_mode
    
    def require_offline(self) -> None:
        """Raise error if offline mode is not enabled."""
        if not self.offline_mode:
            raise RuntimeError(
                "This operation requires offline mode. "
                "Set OFFLINE_MODE=true environment variable."
            )
    
    def require_internet(self) -> None:
        """Raise error if offline mode is enabled."""
        if self.offline_mode:
            raise RuntimeError(
                "This operation requires internet access. "
                "Set OFFLINE_MODE=false environment variable."
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary (for logging/debugging)."""
        return {
            "offline_mode": self.offline_mode,
            "ollama_host": self.ollama_host,
            "ollama_model": self.ollama_model,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "telegram_token": "***" if self.telegram_token else None,
            "chroma_db_dir": str(self.chroma_db_dir),
        }


# Global config instance
config = Config()
