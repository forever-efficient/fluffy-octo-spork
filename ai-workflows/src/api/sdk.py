"""
Python SDK for AI Workflows.

Provides programmatic interface for:
- Initializing AI workflows
- Adding documents
- Running queries
- Custom pipeline creation

Can be imported and used in other Python projects.
Respects OFFLINE_MODE from configuration.
"""

from typing import List, Optional, Dict, Any

from ..config import config
from ..embeddings import ChromaVectorDB, EmbeddingModel
from ..models import OllamaModel
from ..rag import RAGPipeline, DocumentClassifier, DocumentSummarizer


class AIWorkflows:
    """
    High-level SDK for AI Workflows.
    
    Example:
        ```python
        from ai_workflows import AIWorkflows
        
        ai = AIWorkflows()
        ai.add_documents(["Document 1", "Document 2"])
        response = ai.query("What is in the documents?")
        print(response)
        ```
    """
    
    def __init__(
        self,
        collection_name: str = "documents",
        embedding_model: Optional[EmbeddingModel] = None,
        ollama_model: Optional[OllamaModel] = None,
    ):
        """
        Initialize AI Workflows SDK.
        
        Args:
            collection_name: Vector database collection name
            embedding_model: Custom embedding model (uses default if None)
            ollama_model: Custom Ollama model (uses default if None)
        """
        self.collection_name = collection_name
        self.embedding_model = embedding_model or EmbeddingModel()
        self.ollama_model = ollama_model or OllamaModel()
        
        self.vector_db = ChromaVectorDB(
            db_path=str(config.chroma_db_dir),
            embedding_model=self.embedding_model,
        )
        
        self.rag_pipeline = RAGPipeline(
            vector_db=self.vector_db,
            model=self.ollama_model,
            collection_name=collection_name,
        )
        
        self.classifier = DocumentClassifier(
            model=self.ollama_model,
            categories=["general", "technical", "legal", "medical"],
        )
        
        self.summarizer = DocumentSummarizer(model=self.ollama_model)
    
    def add_documents(
        self,
        documents: List[str],
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Add documents to vector database.
        
        Args:
            documents: List of document texts
            ids: Optional document IDs
            metadatas: Optional metadata for each document
            
        Returns:
            Result dict with added IDs
        """
        return self.vector_db.add_documents(
            collection_name=self.collection_name,
            documents=documents,
            ids=ids,
            metadatas=metadatas,
        )
    
    def query(
        self,
        query: str,
        n_results: int = 5,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Run RAG query.
        
        Args:
            query: User query
            n_results: Number of documents to retrieve
            temperature: Model temperature
            system_prompt: Optional system prompt override
            
        Returns:
            Generated response
        """
        return self.rag_pipeline.query(
            query=query,
            n_results=n_results,
            temperature=temperature,
            system_prompt=system_prompt,
        )
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text without RAG.
        
        Args:
            prompt: Input prompt
            temperature: Model temperature
            
        Returns:
            Generated text
        """
        return self.ollama_model.generate(prompt, temperature=temperature)
    
    def classify_document(self, document: str) -> str:
        """
        Classify document into category.
        
        Args:
            document: Document text
            
        Returns:
            Category name
        """
        return self.classifier.classify(document)
    
    def summarize_document(self, document: str, max_length: int = 200) -> str:
        """
        Summarize document.
        
        Args:
            document: Document text
            max_length: Maximum summary length
            
        Returns:
            Summary
        """
        return self.summarizer.summarize(document, max_length=max_length)
    
    def clear_collection(self) -> None:
        """Clear all documents from collection."""
        self.vector_db.delete_collection(self.collection_name)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return config.to_dict()
