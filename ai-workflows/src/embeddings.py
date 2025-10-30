"""
Embedding models and vector database operations.

Handles:
- Local embedding model initialization (using sentence-transformers)
- Chroma vector database connection
- Document chunking and embedding
- Similarity search operations
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Wrapper for local embedding model."""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialize embedding model.
        
        Args:
            model_name: HuggingFace model identifier
            
        Note:
            In offline mode, model must be pre-downloaded and cached.
            Default model produces 384-dimensional embeddings.
        """
        self.model_name = model_name
        self._model = None
    
    def _get_model(self):
        """Lazy load embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each is 384-dim for default model)
        """
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def embed_single(self, text: str) -> List[float]:
        """Embed a single text string."""
        return self.embed([text])[0]


class ChromaVectorDB:
    """Wrapper for Chroma vector database."""
    
    def __init__(self, db_path: str, embedding_model: Optional[EmbeddingModel] = None):
        """
        Initialize Chroma vector database.
        
        Args:
            db_path: Path to local Chroma database directory
            embedding_model: EmbeddingModel instance (creates default if None)
        """
        self.db_path = db_path
        self.embedding_model = embedding_model or EmbeddingModel()
        self._client = None
        self._collection = None
    
    def _get_client(self):
        """Lazy load Chroma client."""
        if self._client is None:
            try:
                import chromadb
                
                # Use new Chroma client configuration
                self._client = chromadb.PersistentClient(
                    path=self.db_path
                )
            except ImportError:
                raise ImportError(
                    "chromadb not installed. "
                    "Install with: pip install chromadb"
                )
        return self._client
    
    def get_or_create_collection(self, name: str):
        """Get or create a Chroma collection."""
        client = self._get_client()
        return client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(
        self, 
        collection_name: str,
        documents: List[str],
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Add documents to collection with embeddings.
        
        Args:
            collection_name: Name of collection
            documents: List of document texts
            ids: Optional list of document IDs (auto-generated if None)
            metadatas: Optional list of metadata dicts
            
        Returns:
            Result dict with added IDs
        """
        collection = self.get_or_create_collection(collection_name)
        
        # Generate embeddings
        embeddings = self.embedding_model.embed(documents)
        
        # Auto-generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Prepare metadata - Chroma requires non-empty dicts
        if metadatas is None:
            metadatas = [{"index": i} for i in range(len(documents))]
        
        # Add to collection
        collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )
        
        logger.info(f"Added {len(documents)} documents to {collection_name}")
        # Return consistent dict structure regardless of Chroma's response
        return {
            "ids": ids,
            "success": True,
        }
    
    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Search for similar documents.
        
        Args:
            collection_name: Name of collection
            query: Query text
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dict with documents, distances, ids, metadatas
        """
        collection = self.get_or_create_collection(collection_name)
        
        # Generate query embedding
        query_embedding = self.embedding_model.embed_single(query)
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )
        
        return results
    
    def delete_by_id(self, collection_name: str, ids: List[str]) -> None:
        """Delete documents by ID."""
        collection = self.get_or_create_collection(collection_name)
        collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from {collection_name}")
    
    def delete_collection(self, collection_name: str) -> None:
        """Delete entire collection."""
        client = self._get_client()
        client.delete_collection(name=collection_name)
        logger.info(f"Deleted collection {collection_name}")
