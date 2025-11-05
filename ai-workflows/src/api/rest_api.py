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
import hashlib
from pathlib import Path
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
from ..legal_chunker import LegalChunker
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


class LegalIngestInput(BaseModel):
    """Input model for legal document ingestion via LegalChunker."""
    text: str
    collection: str = "documents"
    min_tokens: int = 50
    max_tokens: int = 800


class DirectoryIngestInput(BaseModel):
    """Input model to ingest PDFs from the static project data directory using LegalChunker."""
    collection: str = "documents"
    recursive: bool = True
    pattern: str = "*.pdf"
    min_tokens: int = 50
    max_tokens: int = 800
    skip_on_duplicate: bool = True


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

    @app.post("/documents/ingest-legal")
    async def ingest_legal(input_data: LegalIngestInput):
        """
        Ingest a raw legal document text using the LegalChunker and store chunks in ChromaDB.

        Steps:
        - Parse text into hierarchical legal chunks (sections/subsections)
        - Enforce token bounds (min/max) per request
        - Prepare documents/metadatas/ids for ChromaDB
        - Add to the specified vector collection

        Returns:
            Status with counts and the first few IDs as a preview
        """
        try:
            chunker = LegalChunker(min_tokens=input_data.min_tokens, max_tokens=input_data.max_tokens)
            chunks = chunker.parse_document(input_data.text)
            documents, metadatas, ids = LegalChunker.prepare_for_chromadb(chunks)

            if not documents:
                return {
                    "status": "success",
                    "added": 0,
                    "ids": [],
                    "collection": input_data.collection,
                    "chunks": 0,
                }

            result = vector_db.add_documents(
                collection_name=input_data.collection,
                documents=documents,
                ids=ids,
                metadatas=metadatas,
            )
            return {
                "status": "success",
                "added": len(documents),
                "ids": result.get("ids", ids)[:10],  # preview first 10 IDs
                "collection": input_data.collection,
                "chunks": len(documents),
            }
        except Exception as e:
            logger.error(f"Legal ingestion failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/documents/ingest-legal-dir")
    async def ingest_legal_directory(input_data: DirectoryIngestInput):
        """
        Ingest all PDF files from the project's static data directory, parse with
        LegalChunker, and upsert into ChromaDB.

        Idempotency:
        - Compute SHA256 of each file and store in metadata as `file_sha256`.
        - If `skip_on_duplicate` is True and any document exists with same hash in the
          target collection, the file will be skipped.

        Returns a summary with counts and per-file results.
        """
        try:
            # Compute project root: ai-workflows
            project_root = Path(__file__).resolve().parents[2]
            base_path = project_root / "data"
            if not base_path.exists() or not base_path.is_dir():
                raise HTTPException(status_code=400, detail=f"Data directory not found: {base_path}")

            # Gather files
            files: List[Path] = []
            if input_data.recursive:
                files = list(base_path.rglob(input_data.pattern))
            else:
                files = list(base_path.glob(input_data.pattern))

            files = [p for p in files if p.is_file()]
            if not files:
                return {
                    "status": "success",
                    "message": "No files matched in data directory",
                    "scanned_files": 0,
                    "ingested_files": 0,
                    "skipped_files": 0,
                    "collection": input_data.collection,
                    "results": [],
                }

            # Access collection directly to check by metadata filters
            client = vector_db._get_client()
            collection = client.get_or_create_collection(input_data.collection)

            from pypdf import PdfReader  # lazy import to avoid import cost when unused

            def sha256_of_file(path: Path) -> str:
                h = hashlib.sha256()
                with path.open('rb') as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b""):
                        h.update(chunk)
                return h.hexdigest()

            chunker = LegalChunker(min_tokens=input_data.min_tokens, max_tokens=input_data.max_tokens)

            scanned = 0
            ingested = 0
            skipped = 0
            per_file_results: List[Dict[str, Any]] = []

            for fpath in files:
                scanned += 1
                try:
                    file_hash = sha256_of_file(fpath)

                    # Idempotency check
                    if input_data.skip_on_duplicate:
                        existing = collection.get(where={"file_sha256": file_hash}, limit=1)
                        if existing and existing.get("ids"):
                            skipped += 1
                            per_file_results.append({
                                "file": str(fpath),
                                "status": "skipped",
                                "reason": "duplicate",
                                "file_sha256": file_hash,
                            })
                            continue

                    # Extract text
                    reader = PdfReader(str(fpath))
                    pages_text: List[str] = []
                    for page in reader.pages:
                        try:
                            pages_text.append(page.extract_text() or "")
                        except Exception:
                            pages_text.append("")
                    full_text = "\n\n".join(pages_text).strip()

                    if not full_text:
                        skipped += 1
                        per_file_results.append({
                            "file": str(fpath),
                            "status": "skipped",
                            "reason": "no_text",
                        })
                        continue

                    # Chunk using LegalChunker
                    chunks = chunker.parse_document(full_text)
                    documents, metadatas, ids = LegalChunker.prepare_for_chromadb(chunks)

                    # Ensure global uniqueness across files by prefixing with file hash and chunk index
                    ids = [f"{file_hash[:12]}::{i:04d}::{base_id}" for i, base_id in enumerate(ids)]

                    # Enrich metadata with file info and hash for idempotency
                    for md in metadatas:
                        md.update({
                            "source": "pdf",
                            "file_name": fpath.name,
                            "file_path": str(fpath),
                            "file_sha256": file_hash,
                            "page_count": len(pages_text),
                        })

                    if documents:
                        # Use vector_db to ensure embeddings are generated
                        vector_db.add_documents(
                            collection_name=input_data.collection,
                            documents=documents,
                            ids=ids,
                            metadatas=metadatas,
                        )
                        ingested += 1
                        per_file_results.append({
                            "file": str(fpath),
                            "status": "ingested",
                            "chunks": len(documents),
                            "file_sha256": file_hash,
                        })
                    else:
                        skipped += 1
                        per_file_results.append({
                            "file": str(fpath),
                            "status": "skipped",
                            "reason": "no_chunks",
                        })
                except Exception as fe:
                    skipped += 1
                    per_file_results.append({
                        "file": str(fpath),
                        "status": "error",
                        "error": str(fe),
                    })

            return {
                "status": "success",
                "collection": input_data.collection,
                "scanned_files": scanned,
                "ingested_files": ingested,
                "skipped_files": skipped,
                "results": per_file_results[:20],  # preview first 20 files
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Directory legal ingestion failed: {e}")
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
    
    @app.get("/collections")
    async def list_collections():
        """
        List all collections in the database.
        
        Returns:
            List of collections with document counts
        """
        try:
            client = vector_db._get_client()
            collections = client.list_collections()
            result = {
                "status": "success",
                "total": len(collections),
                "collections": [
                    {
                        "name": col.name,
                        "document_count": col.count(),
                    }
                    for col in collections
                ]
            }
            return result
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
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
