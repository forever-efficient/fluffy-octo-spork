-- Complete Legal Assistant Vector Database Setup
-- Creates table schema and search function that your n8n workflow expects
-- Function name: match_legal_documents (not match_documents)
-- Table: legal_documents_vectors with columns: content, embedding, metadata
-- Dimensions: 384 (BAAI/bge-small-en-v1.5 embeddings)

-- Enable pgvector extension (required for vector operations)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the legal_documents_vectors table with correct schema
-- This matches what our PDF processing scripts actually use
CREATE TABLE IF NOT EXISTS legal_documents_vectors (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for metadata queries (used by idempotency checks)
CREATE INDEX IF NOT EXISTS legal_documents_vectors_metadata_title_idx 
ON legal_documents_vectors 
USING gin ((metadata->>'title'));

-- Drop any existing functions first
DROP FUNCTION IF EXISTS match_legal_documents(vector, float, int);
DROP FUNCTION IF EXISTS match_documents(vector, float, int);

-- Create the function your n8n workflow is calling: match_legal_documents
CREATE OR REPLACE FUNCTION match_legal_documents (
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    legal_documents_vectors.id,
    legal_documents_vectors.content,
    legal_documents_vectors.metadata,
    1 - (legal_documents_vectors.embedding <=> query_embedding) AS similarity
  FROM legal_documents_vectors
  WHERE 1 - (legal_documents_vectors.embedding <=> query_embedding) > match_threshold
  ORDER BY legal_documents_vectors.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Create optimized vector similarity search index
CREATE INDEX IF NOT EXISTS legal_documents_vectors_embedding_idx 
ON legal_documents_vectors 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Grant permissions to the function your n8n workflow needs
GRANT EXECUTE ON FUNCTION match_legal_documents(vector(384), float, int) TO anon, authenticated, service_role;