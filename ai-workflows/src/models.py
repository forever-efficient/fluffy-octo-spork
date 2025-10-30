"""
LLM model management and inference.

Handles:
- Ollama model initialization and connection
- Prompt management with configuration
- Model inference with streaming support
- Response generation for RAG workflows
"""

import logging
from typing import List, Optional
import requests

from .config import config

logger = logging.getLogger(__name__)


class OllamaModel:
    """Wrapper for Ollama LLM model."""
    
    def __init__(self, model_name: Optional[str] = None, host: Optional[str] = None):
        """
        Initialize Ollama model connection.
        
        Args:
            model_name: Model identifier (uses OLLAMA_MODEL env var if None)
            host: Ollama host URL (uses OLLAMA_HOST env var if None)
        """
        self.model_name = model_name or config.ollama_model
        self.host = host or config.ollama_host
        self.session = requests.Session()
    
    def _health_check(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = self.session.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def generate(
        self,
        prompt: str,
        stream: bool = False,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """
        Generate response from model.
        
        Args:
            prompt: Input prompt
            stream: Whether to stream response
            temperature: Model temperature (0-1)
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated text response
            
        Raises:
            RuntimeError: If OFFLINE_MODE=true and internet access needed
            RuntimeError: If Ollama service unavailable
        """
        if not self._health_check():
            raise RuntimeError(
                f"Ollama service not available at {self.host}. "
                "Ensure Ollama is running: ollama serve"
            )
        
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": stream,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        try:
            if stream:
                response = self.session.post(url, json=payload, stream=True, timeout=300)
                response.raise_for_status()
                return self._stream_response(response)
            else:
                response = self.session.post(url, json=payload, timeout=300)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(f"Ollama inference failed: {e}")
    
    def _stream_response(self, response) -> str:
        """Process streaming response from Ollama."""
        full_response = ""
        for line in response.iter_lines():
            if line:
                import json
                try:
                    chunk = json.loads(line)
                    full_response += chunk.get("response", "")
                except json.JSONDecodeError:
                    continue
        return full_response


class PromptTemplate:
    """Template for generating prompts with context."""
    
    def __init__(self, template: str, variables: List[str]):
        """
        Initialize prompt template.
        
        Args:
            template: Template string with {variable} placeholders
            variables: List of variable names
        """
        self.template = template
        self.variables = variables
    
    def format(self, **kwargs) -> str:
        """Format template with provided variables."""
        # Validate all required variables are provided
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        
        return self.template.format(**kwargs)


class RAGModel:
    """High-level model for RAG (Retrieval-Augmented Generation) tasks."""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        """
        Initialize RAG model.
        
        Args:
            model_name: Ollama model name
            system_prompt: System prompt for model behavior
        """
        self.model = OllamaModel(model_name)
        self.system_prompt = system_prompt or (
            "You are a helpful AI assistant. "
            "Use the provided context to answer questions accurately."
        )
    
    def generate_with_context(
        self,
        query: str,
        context_documents: List[str],
        temperature: float = 0.7,
    ) -> str:
        """
        Generate response using query and retrieved context documents.
        
        Args:
            query: User query
            context_documents: List of retrieved documents for context
            temperature: Model temperature
            
        Returns:
            Generated response
        """
        # Build context section
        context = "\n\n".join([
            f"[Document {i+1}]\n{doc}"
            for i, doc in enumerate(context_documents)
        ])
        
        # Build full prompt
        prompt = f"""System: {self.system_prompt}

Context:
{context}

User Query: {query}

Answer:"""
        
        return self.model.generate(prompt, temperature=temperature)
