# Legal Assistant n8n Bot - Advanced Configuration Guide

## AI Model Alternatives

### 1. Hugging Face Models (Free)

#### Text Classification Models:
```javascript
// In the "Validate Content" node
{
  "model": "facebook/bart-large-mnli",
  "inputs": "This message is about legal matters.",
  "parameters": {
    "candidate_labels": ["legal", "criminal", "unrelated"]
  }
}
```

#### Conversation Models:
```javascript
// In the "AI Legal Analysis" node
{
  "model": "microsoft/DialoGPT-large",
  "inputs": "Previous conversation context + current question",
  "parameters": {
    "max_length": 1000,
    "temperature": 0.3,
    "do_sample": true
  }
}
```

### 2. OpenAI API (Free Tier)

```javascript
// Alternative configuration for OpenAI
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "system", 
      "content": "You are a legal AI assistant..."
    },
    {
      "role": "user", 
      "content": "user question here"
    }
  ],
  "max_tokens": 1000,
  "temperature": 0.3
}
```

## Database Advanced Queries

### User Analytics Query:
```sql
-- Get user engagement statistics
SELECT 
    u.user_id,
    COUNT(u.id) as total_conversations,
    COUNT(r.id) as rejected_requests,
    AVG(LENGTH(u.conversation_history)) as avg_conversation_length,
    MAX(u.updated_at) as last_activity
FROM user_conversations u
LEFT JOIN rejected_requests r ON u.user_id = r.user_id
GROUP BY u.user_id
ORDER BY total_conversations DESC;
```

### Legal Document Relevance:
```sql
-- Update document relevance based on usage
UPDATE legal_documents 
SET relevance_score = relevance_score + 1 
WHERE id IN (
    SELECT DISTINCT d.id 
    FROM legal_documents d
    JOIN usage_logs u ON u.document_id = d.id
    WHERE u.created_at > NOW() - INTERVAL '7 days'
);
```

## Custom n8n Nodes Configuration

### Enhanced Voice Processing Node:
```javascript
// Custom code for better voice transcription
const items = [];
for (const item of $input.all()) {
    if (item.json.message && item.json.message.voice) {
        const voiceFile = item.json.message.voice;
        
        // Enhanced voice processing
        const enhancedVoice = {
            file_id: voiceFile.file_id,
            duration: voiceFile.duration,
            mime_type: voiceFile.mime_type || 'audio/ogg',
            file_size: voiceFile.file_size,
            // Add metadata for better processing
            user_id: item.json.message.from.id,
            chat_id: item.json.message.chat.id,
            timestamp: new Date().toISOString()
        };
        
        items.push({
            json: enhancedVoice
        });
    }
}
return items;
```

### Legal Context Enrichment:
```javascript
// Enhanced legal context preparation
const items = [];
const message = $('Normalize Message').item.json;
const docs = $('Get Legal Documents').all();
const memory = $('Get Conversation Memory').item.json;

// Extract legal entities and concepts
const legalEntities = extractLegalEntities(message.messageText);
const relevantDocs = filterDocumentsByRelevance(docs, legalEntities);

// Build enhanced context
const enhancedContext = {
    originalMessage: message.messageText,
    legalEntities: legalEntities,
    relevantStatutes: relevantDocs.filter(d => d.type === 'statute'),
    relevantCases: relevantDocs.filter(d => d.type === 'case_law'),
    conversationHistory: memory.conversation_history || '',
    jurisdiction: detectJurisdiction(message.messageText),
    urgencyLevel: assessUrgency(message.messageText)
};

function extractLegalEntities(text) {
    const patterns = {
        statutes: /\b\d+\s+U\.?S\.?C\.?\s+§?\s*\d+/gi,
        cases: /\b[A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+/gi,
        amendments: /\b(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|\d+)(st|nd|rd|th)?\s+Amendment/gi
    };
    
    return {
        statutes: text.match(patterns.statutes) || [],
        cases: text.match(patterns.cases) || [],
        amendments: text.match(patterns.amendments) || []
    };
}

items.push({ json: enhancedContext });
return items;
```

## Advanced Supabase Configuration

### Real-time Subscriptions:
```sql
-- Create real-time subscription for urgent legal requests
CREATE OR REPLACE FUNCTION notify_urgent_request()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.urgency_level = 'high' THEN
        PERFORM pg_notify('urgent_legal_request', json_build_object(
            'user_id', NEW.user_id,
            'message', NEW.message_text,
            'timestamp', NEW.timestamp
        )::text);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER urgent_request_trigger
    AFTER INSERT ON user_conversations
    FOR EACH ROW
    EXECUTE FUNCTION notify_urgent_request();
```

### Performance Optimization:
```sql
-- Materialized view for document search
CREATE MATERIALIZED VIEW legal_document_search AS
SELECT 
    id,
    title,
    type,
    content,
    to_tsvector('english', title || ' ' || content) as search_vector,
    relevance_score
FROM legal_documents
WHERE content IS NOT NULL;

CREATE INDEX idx_legal_document_search_vector 
ON legal_document_search USING GIN(search_vector);

-- Refresh the view regularly
REFRESH MATERIALIZED VIEW legal_document_search;
```

## Security Enhancements

### Rate Limiting Configuration:
```javascript
// Enhanced rate limiting in n8n
const rateLimitConfig = {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests per windowMs
    skipSuccessfulRequests: false,
    skipFailedRequests: false,
    keyGenerator: (req) => {
        // Use Telegram user ID for rate limiting
        return req.body?.message?.from?.id || req.ip;
    },
    handler: (req, res) => {
        res.status(429).json({
            error: 'Too many requests',
            message: 'Please wait before sending another message'
        });
    }
};
```

### Input Sanitization:
```javascript
// Sanitize user input
function sanitizeInput(text) {
    // Remove potentially harmful characters
    const sanitized = text
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/javascript:/gi, '')
        .replace(/on\w+="[^"]*"/gi, '')
        .trim();
    
    // Limit length
    return sanitized.substring(0, 4000);
}

// Apply to all user inputs
const sanitizedMessage = sanitizeInput($json.message.text || '');
```

## Monitoring and Analytics

### Custom Metrics Collection:
```javascript
// Enhanced metrics collection
const metrics = {
    timestamp: new Date().toISOString(),
    user_id: $json.userId,
    chat_id: $json.chatId,
    message_type: $json.message.voice ? 'voice' : 'text',
    message_length: $json.messageText.length,
    response_time: Date.now() - $json.startTime,
    ai_model_used: 'huggingface-dialogpt',
    documents_retrieved: $json.documentsCount,
    conversation_turn: $json.conversationTurn,
    legal_entities_found: $json.legalEntities.length,
    satisfaction_score: null // To be updated later
};

// Store metrics
await $executeWorkflow('Store Metrics', [{ json: metrics }]);
```

### Error Tracking:
```javascript
// Enhanced error handling and tracking
try {
    // AI processing logic here
    const result = await processLegalQuery($json);
    return [{ json: result }];
} catch (error) {
    // Log detailed error information
    const errorLog = {
        timestamp: new Date().toISOString(),
        user_id: $json.userId,
        chat_id: $json.chatId,
        error_type: error.name,
        error_message: error.message,
        stack_trace: error.stack,
        input_data: $json,
        workflow_node: $node.name,
        execution_id: $executionId
    };
    
    // Store error log
    await $executeWorkflow('Log Error', [{ json: errorLog }]);
    
    // Return user-friendly error response
    return [{
        json: {
            error: true,
            message: "I encountered an issue processing your request. Please try again later.",
            timestamp: new Date().toISOString()
        }
    }];
}
```

## Integration with External Legal APIs

### Court Listener API Integration:
```javascript
// Enhanced Court Listener integration
async function searchCourtOpinions(query, jurisdiction = 'federal') {
    const searchParams = {
        q: query,
        type: 'o', // opinions
        order_by: '-date_created',
        court__jurisdiction: jurisdiction,
        per_page: 5
    };
    
    const response = await fetch(
        `https://www.courtlistener.com/api/rest/v3/search/?${new URLSearchParams(searchParams)}`,
        {
            headers: {
                'Authorization': `Token ${process.env.COURTLISTENER_API_KEY}`,
                'User-Agent': 'Legal-Assistant-Bot/1.0'
            }
        }
    );
    
    return await response.json();
}
```

### OpenStates API Integration:
```javascript
// State legislation search
async function searchStateLegislation(query, state = 'all') {
    const response = await fetch(
        `https://openstates.org/graphql`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': process.env.OPENSTATES_API_KEY
            },
            body: JSON.stringify({
                query: `
                    query($state: String!, $query: String!) {
                        bills(
                            jurisdiction: $state,
                            searchQuery: $query,
                            first: 5
                        ) {
                            edges {
                                node {
                                    id
                                    title
                                    description
                                    latestAction {
                                        description
                                        date
                                    }
                                }
                            }
                        }
                    }
                `,
                variables: { state, query }
            })
        }
    );
    
    return await response.json();
}
```

This advanced configuration guide provides additional customization options for power users who want to extend the legal assistant bot's capabilities.