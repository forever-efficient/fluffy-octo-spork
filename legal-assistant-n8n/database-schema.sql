-- Supabase Database Schema for Legal Assistant Bot

-- Table for storing rejected requests and their reasons
CREATE TABLE rejected_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    message_text TEXT NOT NULL,
    reason TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for storing user conversation history for memory
CREATE TABLE user_conversations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    conversation_history TEXT DEFAULT '',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, chat_id)
);

-- Table for storing legal documents and PDFs
CREATE TABLE legal_documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    type VARCHAR(100) NOT NULL, -- 'statute', 'case_law', 'regulation', 'guideline'
    content TEXT NOT NULL,
    source_url VARCHAR(1000),
    jurisdiction VARCHAR(200), -- 'federal', 'state', 'local'
    relevance_score INTEGER DEFAULT 1,
    file_path VARCHAR(1000), -- Path to PDF in storage
    metadata JSONB, -- Additional metadata like date, court, etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for storing API endpoints and external resources
CREATE TABLE legal_apis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    api_key_required BOOLEAN DEFAULT FALSE,
    description TEXT,
    endpoints JSONB, -- Store endpoint configurations
    rate_limit INTEGER, -- Requests per minute/hour
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'deprecated'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX idx_rejected_requests_user_chat ON rejected_requests(user_id, chat_id);
CREATE INDEX idx_rejected_requests_timestamp ON rejected_requests(timestamp);
CREATE INDEX idx_user_conversations_user_chat ON user_conversations(user_id, chat_id);
CREATE INDEX idx_legal_documents_type ON legal_documents(type);
CREATE INDEX idx_legal_documents_relevance ON legal_documents(relevance_score DESC);
CREATE INDEX idx_legal_documents_jurisdiction ON legal_documents(jurisdiction);

-- Row Level Security (RLS) policies
ALTER TABLE rejected_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE legal_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE legal_apis ENABLE ROW LEVEL SECURITY;

-- Create policies for service role access (n8n will use service role)
CREATE POLICY "Service role can access all rejected_requests" ON rejected_requests
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all user_conversations" ON user_conversations
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all legal_documents" ON legal_documents
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all legal_apis" ON legal_apis
    FOR ALL USING (auth.role() = 'service_role');

-- Insert sample legal documents
INSERT INTO legal_documents (title, type, content, jurisdiction, relevance_score) VALUES
(
    'Fourth Amendment - Search and Seizure',
    'constitutional',
    'The right of the people to be secure in their persons, houses, papers, and effects, against unreasonable searches and seizures, shall not be violated, and no Warrants shall issue, but upon probable cause, supported by Oath or affirmation, and particularly describing the place to be searched, and the persons or things to be seized.',
    'federal',
    10
),
(
    'Miranda Rights Requirements',
    'case_law',
    'Miranda v. Arizona (1966) established that suspects must be informed of their rights before custodial interrogation. The warnings must include: right to remain silent, statements may be used against them, right to an attorney, and right to appointed counsel if indigent.',
    'federal',
    9
),
(
    'Probable Cause Standard',
    'case_law',
    'Probable cause exists when facts and circumstances would lead a reasonable person to believe that a crime has been committed and that evidence of the crime exists in the place to be searched.',
    'federal',
    8
);

-- Insert sample API configurations
INSERT INTO legal_apis (name, base_url, description, endpoints) VALUES
(
    'Free Law Project API',
    'https://www.courtlistener.com/api/rest/v3/',
    'Access to federal and state court opinions, statutes, and regulations',
    '{"opinions": "/opinions/", "statutes": "/statutes/", "search": "/search/"}'
),
(
    'Open States API',
    'https://openstates.org/api/v3/',
    'State legislature information and bills',
    '{"bills": "/bills/", "legislators": "/people/", "committees": "/committees/"}'
);