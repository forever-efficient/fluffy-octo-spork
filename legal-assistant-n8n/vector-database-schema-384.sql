-- Vector Database Schema for 384-Dimensional Embeddings
-- Legal Assistant Bot - Updated for HuggingFace BAAI/bge-small-en-v1.5

-- Drop existing table to avoid conflicts
DROP TABLE IF EXISTS legal_documents_vectors CASCADE;

-- Create the legal_documents_vectors table with 384-dimensional vectors
CREATE TABLE legal_documents_vectors (
    id BIGSERIAL PRIMARY KEY,
    document_id UUID REFERENCES legal_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX legal_documents_vectors_document_id_idx ON legal_documents_vectors(document_id);
CREATE INDEX legal_documents_vectors_chunk_index_idx ON legal_documents_vectors(chunk_index);

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