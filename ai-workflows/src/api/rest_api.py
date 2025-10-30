"""
REST API entry point for AI Workflows.

Provides HTTP interface for:
- Document ingestion and embedding
- Query/RAG operations
- Model inference
- Health checks
- Configuration info

Respects OFFLINE_MODE from configuration.
"""

import logging
from typing import List, Dict, Any, Optional

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from ..config import config
from ..embeddings import ChromaVectorDB, EmbeddingModel
from ..models import OllamaModel
from ..rag import RAGPipeline

logger = logging.getLogger(__name__)


class DocumentInput(BaseModel):
    """Input model for adding documents."""
    texts: List[str]
    ids: Optional[List[str]] = None
    metadatas: Optional[List[Dict[str, Any]]] = None
    collection: str = "documents"


class QueryInput(BaseModel):
    """Input model for RAG queries."""
    query: str
    n_results: int = 5
    collection: str = "documents"
    temperature: float = 0.7


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    offline_mode: bool
    ollama_available: bool
    config: Dict[str, Any]


def create_app() -> Optional[FastAPI]:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI app instance or None if FastAPI not available
    """
    if not HAS_FASTAPI:
        logger.error("FastAPI not installed. Install with: pip install fastapi uvicorn")
        return None
    
    app = FastAPI(
        title="AI Workflows API",
        description="Local, offline-capable AI workflows",
        version="0.1.0",
    )
    
    # Initialize components
    embedding_model = EmbeddingModel()
    vector_db = ChromaVectorDB(
        db_path=str(config.chroma_db_dir),
        embedding_model=embedding_model,
    )
    ollama_model = OllamaModel()
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Check API and service health."""
        ollama_ok = ollama_model._health_check()
        
        return HealthResponse(
            status="ok" if ollama_ok else "degraded",
            offline_mode=config.offline_mode,
            ollama_available=ollama_ok,
            config=config.to_dict(),
        )
    
    @app.post("/documents/add")
    async def add_documents(input_data: DocumentInput):
        """
        Add documents to vector database.
        
        Args:
            texts: List of document texts
            ids: Optional document IDs
            metadatas: Optional metadata for each document
            collection: Collection name (default: documents)
            
        Returns:
            Result with added document IDs
        """
        try:
            result = vector_db.add_documents(
                collection_name=input_data.collection,
                documents=input_data.texts,
                ids=input_data.ids,
                metadatas=input_data.metadatas,
            )
            return {
                "status": "success",
                "added": len(input_data.texts),
                "ids": result.get("ids", []),
            }
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/query")
    async def query_rag(input_data: QueryInput):
        """
        Execute RAG query with document retrieval and generation.
        
        Args:
            query: User query
            n_results: Number of documents to retrieve
            collection: Collection name (default: documents)
            temperature: Model temperature
            
        Returns:
            Generated response with context
        """
        try:
            # Create RAG pipeline for the requested collection
            rag = RAGPipeline(
                vector_db=vector_db,
                model=ollama_model,
                collection_name=input_data.collection,
            )
            response = rag.query(
                query=input_data.query,
                n_results=input_data.n_results,
                temperature=input_data.temperature,
            )
            return {
                "status": "success",
                "response": response,
                "query": input_data.query,
            }
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/generate")
    async def generate(prompt: str, temperature: float = 0.7):
        """
        Generate text without RAG (direct model inference).
        
        Args:
            prompt: Input prompt
            temperature: Model temperature
            
        Returns:
            Generated text
        """
        try:
            response = ollama_model.generate(prompt, temperature=temperature)
            return {
                "status": "success",
                "response": response,
                "model": ollama_model.model_name,
            }
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/config")
    async def get_config():
        """Get current configuration."""
        return config.to_dict()
    
    @app.delete("/collections/{collection_name}")
    async def delete_collection(collection_name: str):
        """
        Delete entire collection and all documents.
        
        Args:
            collection_name: Name of collection to delete
            
        Returns:
            Status message
        """
        try:
            vector_db.delete_collection(collection_name)
            return {
                "status": "success",
                "message": f"Collection '{collection_name}' deleted"
            }
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/documents")
    async def delete_documents(ids: List[str], collection: str = "documents"):
        """
        Delete specific documents by ID.
        
        Args:
            ids: List of document IDs to delete
            collection: Collection name (default: documents)
            
        Returns:
            Status message with count
        """
        try:
            vector_db.delete_by_id(collection, ids)
            return {
                "status": "success",
                "deleted": len(ids),
                "ids": ids
            }
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    if app:
        uvicorn.run(app, host=config.api_host, port=config.api_port)
