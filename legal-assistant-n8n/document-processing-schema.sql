-- Document Processing Logs Table for PDF ingestion tracking
-- Execute this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS document_processing_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    file_name TEXT NOT NULL,
    title TEXT NOT NULL,
    document_type TEXT DEFAULT 'legal_document',
    category TEXT DEFAULT 'general',
    jurisdiction TEXT DEFAULT 'unknown',
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    chunks_created INTEGER DEFAULT 0,
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    error_message TEXT,
    file_size INTEGER DEFAULT 0,
    uploaded_by TEXT DEFAULT 'system',
    source TEXT DEFAULT 'manual_upload',
    tags JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_document_processing_logs_status ON document_processing_logs(processing_status);
CREATE INDEX IF NOT EXISTS idx_document_processing_logs_processed_at ON document_processing_logs(processed_at);
CREATE INDEX IF NOT EXISTS idx_document_processing_logs_file_name ON document_processing_logs(file_name);
CREATE INDEX IF NOT EXISTS idx_document_processing_logs_category ON document_processing_logs(category);

-- Row Level Security
ALTER TABLE document_processing_logs ENABLE ROW LEVEL SECURITY;

-- Policy for service role (full access)
CREATE POLICY "Service role full access on document_processing_logs" 
ON document_processing_logs 
FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- Policy for authenticated users (read access)
CREATE POLICY "Authenticated users can read document_processing_logs" 
ON document_processing_logs 
FOR SELECT 
TO authenticated 
USING (true);

-- Updated at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_document_processing_logs_updated_at 
BEFORE UPDATE ON document_processing_logs 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add helpful comments
COMMENT ON TABLE document_processing_logs IS 'Tracks PDF document processing operations for legal assistant bot';
COMMENT ON COLUMN document_processing_logs.chunks_created IS 'Number of text chunks created during processing';
COMMENT ON COLUMN document_processing_logs.processing_status IS 'Current status of document processing';
COMMENT ON COLUMN document_processing_logs.tags IS 'JSON array of tags associated with the document';