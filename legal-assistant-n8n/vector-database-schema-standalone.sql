-- Simplified Vector Database Schema for PDF Processing
-- For standalone PDF processing without legal_documents table dependency

-- Drop existing table to avoid conflicts
DROP TABLE IF EXISTS legal_documents_vectors CASCADE;

-- Create the legal_documents_vectors table with 384-dimensional vectors
-- Made document_id optional for standalone PDF processing
CREATE TABLE legal_documents_vectors (
    id BIGSERIAL PRIMARY KEY,
    document_id UUID DEFAULT NULL, -- Made optional for standalone PDF processing
    chunk_text TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX legal_documents_vectors_chunk_index_idx ON legal_documents_vectors(chunk_index);
CREATE INDEX legal_documents_vectors_document_id_idx ON legal_documents_vectors(document_id) WHERE document_id IS NOT NULL;

-- Create vector similarity search index using HNSW
CREATE INDEX legal_documents_vectors_embedding_idx ON legal_documents_vectors 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Enable Row Level Security
ALTER TABLE legal_documents_vectors ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
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

-- Grant necessary permissions
GRANT ALL ON legal_documents_vectors TO authenticated;
GRANT USAGE ON SEQUENCE legal_documents_vectors_id_seq TO authenticated;