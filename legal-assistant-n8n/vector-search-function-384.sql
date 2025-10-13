-- Vector Search Function for 384-Dimensional Embeddings
-- Legal Assistant Bot - Updated for HuggingFace BAAI/bge-small-en-v1.5

-- Drop existing function to avoid conflicts
DROP FUNCTION IF EXISTS match_legal_documents(vector(1536), float, int);
DROP FUNCTION IF EXISTS match_legal_documents(vector(384), float, int);

-- Create the vector similarity search function for 384-dimensional embeddings
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

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION match_legal_documents(vector(384), float, int) TO authenticated;