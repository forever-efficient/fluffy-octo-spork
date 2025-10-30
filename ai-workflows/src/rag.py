"""
RAG (Retrieval-Augmented Generation) pipeline orchestration.

Handles:
- Document retrieval from vector database
- Prompt construction with context
- LLM inference coordination
- Pipeline workflows (e.g., document classification, Q&A)
"""

import logging
from typing import List, Optional

from .embeddings import ChromaVectorDB
from .models import OllamaModel, RAGModel

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Standard RAG pipeline: retrieve documents, augment prompt, generate response."""
    
    def __init__(
        self,
        vector_db: ChromaVectorDB,
        model: OllamaModel,
        collection_name: str = "documents",
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            vector_db: ChromaVectorDB instance for retrieval
            model: OllamaModel instance for generation
            collection_name: Name of vector collection to search
        """
        self.vector_db = vector_db
        self.model = model
        self.collection_name = collection_name
    
    def query(
        self,
        query: str,
        n_results: int = 5,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Execute RAG query.
        
        Args:
            query: User query
            n_results: Number of documents to retrieve
            system_prompt: Optional system prompt override
            temperature: Model temperature
            
        Returns:
            Generated response with retrieved context
        """
        # Step 1: Retrieve relevant documents
        search_results = self.vector_db.search(
            collection_name=self.collection_name,
            query=query,
            n_results=n_results,
        )
        
        # Extract documents and distances
        documents = search_results.get("documents", [[]])[0]
        distances = search_results.get("distances", [[]])[0]
        
        if not documents:
            logger.warning("No documents retrieved for query")
            return "No relevant documents found to answer your question."
        
        # Log retrieval stats
        logger.info(f"Retrieved {len(documents)} documents (distances: {distances})")
        
        # Step 2: Create RAG model with system prompt
        rag_model = RAGModel(model_name=self.model.model_name, system_prompt=system_prompt)
        
        # Step 3: Generate response with context
        response = rag_model.generate_with_context(
            query=query,
            context_documents=documents,
            temperature=temperature,
        )
        
        return response


class DocumentClassifier:
    """Classify documents into categories using LLM."""
    
    def __init__(
        self,
        model: OllamaModel,
        categories: List[str],
    ):
        """
        Initialize document classifier.
        
        Args:
            model: OllamaModel instance
            categories: List of category names to classify into
        """
        self.model = model
        self.categories = categories
    
    def classify(self, document: str) -> str:
        """
        Classify document into one of the categories.
        
        Args:
            document: Document text to classify
            
        Returns:
            Category name
        """
        categories_str = ", ".join(self.categories)
        
        prompt = f"""Classify the following document into one of these categories: {categories_str}

Document:
{document}

Category:"""
        
        response = self.model.generate(prompt, temperature=0.3)
        
        # Extract category from response (first word)
        category = response.strip().split()[0]
        
        # Ensure it's a valid category
        if category not in self.categories:
            logger.warning(f"Invalid category '{category}', defaulting to first")
            category = self.categories[0]
        
        return category


class DocumentSummarizer:
    """Summarize documents using LLM."""
    
    def __init__(self, model: OllamaModel):
        """
        Initialize summarizer.
        
        Args:
            model: OllamaModel instance
        """
        self.model = model
    
    def summarize(
        self,
        document: str,
        max_length: int = 200,
    ) -> str:
        """
        Summarize document.
        
        Args:
            document: Document text to summarize
            max_length: Maximum summary length (approximate)
            
        Returns:
            Document summary
        """
        prompt = f"""Summarize the following document in approximately {max_length} words:

Document:
{document}

Summary:"""
        
        response = self.model.generate(prompt, temperature=0.5)
        return response.strip()
