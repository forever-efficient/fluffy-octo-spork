"""
Command-line interface entry point for AI Workflows.

Provides CLI commands for:
- Document ingestion
- Running RAG queries
- Managing collections
- Health checks

Respects OFFLINE_MODE from configuration.
"""

import logging
from typing import Optional, List
import json

from ..config import config
from ..embeddings import ChromaVectorDB, EmbeddingModel
from ..models import OllamaModel
from ..rag import RAGPipeline

logger = logging.getLogger(__name__)


class CLI:
    """Command-line interface for AI Workflows."""
    
    def __init__(self):
        """Initialize CLI components."""
        self.embedding_model = EmbeddingModel()
        self.vector_db = ChromaVectorDB(
            db_path=str(config.chroma_db_dir),
            embedding_model=self.embedding_model,
        )
        self.ollama_model = OllamaModel()
        self.rag_pipeline = RAGPipeline(
            vector_db=self.vector_db,
            model=self.ollama_model,
        )
    
    def add_documents(
        self,
        texts: List[str],
        collection: str = "documents",
        ids: Optional[List[str]] = None,
    ) -> None:
        """
        Add documents to vector database.
        
        Args:
            texts: List of document texts
            collection: Collection name
            ids: Optional document IDs
        """
        try:
            result = self.vector_db.add_documents(
                collection_name=collection,
                documents=texts,
                ids=ids,
            )
            print(f"✓ Added {len(texts)} documents to '{collection}'")
            print(f"  IDs: {result.get('ids', [])}")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def query(
        self,
        query: str,
        n_results: int = 5,
        collection: str = "documents",
        temperature: float = 0.7,
    ) -> str:
        """
        Execute RAG query.
        
        Args:
            query: User query
            n_results: Number of documents to retrieve
            collection: Collection name
            temperature: Model temperature
            
        Returns:
            Generated response
        """
        try:
            print(f"\n🔍 Query: {query}")
            response = self.rag_pipeline.query(
                query=query,
                n_results=n_results,
                temperature=temperature,
            )
            print(f"\n💬 Response:\n{response}\n")
            return response
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
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
        try:
            response = self.ollama_model.generate(prompt, temperature=temperature)
            print(f"Response:\n{response}\n")
            return response
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def health(self) -> None:
        """Check system health."""
        print("\n📊 System Health\n")
        print(f"Offline Mode: {config.offline_mode}")
        print(f"Ollama Host: {self.ollama_model.host}")
        print(f"Ollama Model: {self.ollama_model.model_name}")
        
        if self.ollama_model._health_check():
            print("✓ Ollama: Available")
        else:
            print("✗ Ollama: Unavailable")
        
        print(f"Chroma DB: {config.chroma_db_dir}")
        print()


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AI Workflows - Local, offline-capable AI system"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Run RAG query")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument("--collection", default="documents", help="Collection name")
    query_parser.add_argument("--n-results", type=int, default=5, help="Number of results")
    query_parser.add_argument("--temperature", type=float, default=0.7, help="Model temperature")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate text without RAG")
    gen_parser.add_argument("prompt", help="Input prompt")
    gen_parser.add_argument("--temperature", type=float, default=0.7, help="Model temperature")
    
    # Health command
    subparsers.add_parser("health", help="Check system health")
    
    # Add documents command
    add_parser = subparsers.add_parser("add-documents", help="Add documents to database")
    add_parser.add_argument("--file", help="JSON file with documents")
    add_parser.add_argument("--collection", default="documents", help="Collection name")
    
    args = parser.parse_args()
    cli = CLI()
    
    if args.command == "query":
        cli.query(
            query=args.query,
            collection=args.collection,
            n_results=args.n_results,
            temperature=args.temperature,
        )
    elif args.command == "generate":
        cli.generate(prompt=args.prompt, temperature=args.temperature)
    elif args.command == "health":
        cli.health()
    elif args.command == "add-documents":
        if not args.file:
            print("Error: --file required")
            return
        with open(args.file) as f:
            data = json.load(f)
        texts = data.get("texts", [])
        ids = data.get("ids")
        cli.add_documents(texts=texts, collection=args.collection, ids=ids)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
