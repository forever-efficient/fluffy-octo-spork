-- Complete Migration Script for Vector Database
-- Migrates from 1536-dimensional (OpenAI) to 384-dimensional (HuggingFace) embeddings

-- Step 1: Backup existing data (optional)
-- CREATE TABLE legal_documents_vectors_backup AS SELECT * FROM legal_documents_vectors;

-- Step 2: Drop existing constraints and indexes
DROP INDEX IF EXISTS legal_documents_vectors_embedding_idx;

-- Step 3: Drop and recreate table with new vector dimensions
DROP TABLE IF EXISTS legal_documents_vectors CASCADE;

-- Step 4: Create new table structure (384 dimensions)
CREATE TABLE legal_documents_vectors (
    id BIGSERIAL PRIMARY KEY,
    document_id UUID REFERENCES legal_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 5: Create optimized indexes
CREATE INDEX legal_documents_vectors_document_id_idx ON legal_documents_vectors(document_id);
CREATE INDEX legal_documents_vectors_chunk_index_idx ON legal_documents_vectors(chunk_index);
CREATE INDEX legal_documents_vectors_embedding_idx ON legal_documents_vectors 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Step 6: Enable Row Level Security
ALTER TABLE legal_documents_vectors ENABLE ROW LEVEL SECURITY;

-- Step 7: Create RLS policies
CREATE POLICY "Legal documents vectors are viewable by authenticated users" 
    ON legal_documents_vectors FOR SELECT 
    TO authenticated 
    USING (true);

CREATE POLICY "Legal documents vectors are insertable by authenticated users" 
    ON legal_documents_vectors FOR INSERT 
    TO authenticated 
    WITH CHECK (true);

CREATE POLICY "Legal documents vectors are updatable by authenticated users" 
    ON legal_documents_vectors FOR UPDATE 
    TO authenticated 
    USING (true);

CREATE POLICY "Legal documents vectors are deletable by authenticated users" 
    ON legal_documents_vectors FOR DELETE 
    TO authenticated 
    USING (true);

-- Step 8: Grant permissions
GRANT ALL ON legal_documents_vectors TO authenticated;
GRANT USAGE ON SEQUENCE legal_documents_vectors_id_seq TO authenticated;

-- Step 9: Drop old function and create new one
DROP FUNCTION IF EXISTS match_legal_documents(vector(1536), float, int);
DROP FUNCTION IF EXISTS match_legal_documents(vector(384), float, int);

CREATE OR REPLACE FUNCTION match_legal_documents(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.3,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id bigint,
    document_id uuid,
    chunk_text text,
    similarity float,
    chunk_index integer,
    metadata jsonb
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ldv.id,
        ldv.document_id,
        ldv.chunk_text,
        1 - (ldv.embedding <=> query_embedding) AS similarity,
        ldv.chunk_index,
        ldv.metadata
    FROM legal_documents_vectors ldv
    WHERE 1 - (ldv.embedding <=> query_embedding) > match_threshold
    ORDER BY ldv.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Step 10: Grant function permissions
GRANT EXECUTE ON FUNCTION match_legal_documents(vector(384), float, int) TO authenticated;

-- Migration Complete!
-- Note: You will need to re-process all documents using the new 384-dimensional embedding model
-- Run the process-pdfs-from-storage.py script to populate the table with new embeddings