# Legal Assistant n8n Bot

A comprehensive n8n automation workflow that creates a Telegram bot for advanced legal and criminal law assistance. The bot validates incoming messages, processes legal questions using AI with RAG (Retrieval-Augmented Generation), and maintains conversation memory for follow-up questions.

## 🆕 **Latest Enhancements**

- 🔧 **Fixed Vector Search**: Resolved embedding model mismatch for accurate legal document retrieval
- 🏛️ **Legal Term Interpreter**: Advanced legal terminology analysis and interpretation
- 🌐 **Multi-Source HTML Parsing**: Automatic parsing of Google Scholar, Cornell Law, and FindLaw
- 🎯 **Enhanced RAG**: Improved context retrieval with BAAI/bge-small-en-v1.5 embeddings
- 📊 **Optimized AI Context**: Smarter context preparation for better legal responses

## Features

- 🤖 **Telegram Integration**: Receives text and voice messages
- 🛡️ **Content Guardrails**: AI-powered validation for legal/crime topics only
- 🎯 **Scenario Analysis**: Analyzes criminal scenarios (e.g., "a wife smashes her husband's phone")
- ❓ **Direct Legal Questions**: Answers specific legal questions (e.g., "What are Miranda rights?")
- 🧠 **AI Legal Analysis**: Uses Groq AI models for comprehensive legal reasoning
- 📚 **Document Access**: Integrates with legal PDFs and external legal databases
- 🔍 **Vector Search**: Advanced semantic search through legal documents using BAAI/bge-small-en-v1.5 embeddings
- 🎯 **RAG Integration**: Retrieval-Augmented Generation for context-aware legal responses
- 💾 **Conversation Memory**: Maintains context for follow-up questions
- 📊 **Database Logging**: Tracks rejected requests and conversation history
- 🔒 **Security**: Rate limiting and user management

## Architecture

```
Telegram Message → Content Validation → Legal Term Interpreter → Vector Search → AI Analysis → Response Formatting
                ↓                   ↓                        ↓              ↓               ↓
            Voice-to-Text      Legal Analysis         Document Retrieval   Multi-Source    Database
                                                     (BAAI/bge-small)     HTML Parsing     Logging
                                                                        (Scholar/Cornell)
```

**Vector Search Pipeline:**
- **HuggingFace Embeddings**: BAAI/bge-small-en-v1.5 (384-dimensional)
- **Semantic Similarity**: Cosine distance matching with configurable thresholds
- **Document Chunking**: Optimized text chunks for better retrieval accuracy
- **Multi-Source Integration**: Real-time legal database queries and parsing

## Quick Start

### 🎯 **For Self-Hosted n8n Users (Recommended)**

**📍 WHERE TO RUN EVERYTHING:**
- **Setup Script**: Run on **your local machine** (where you downloaded these files)
- **Workflow Import**: Done in **your n8n web interface** 
- **Webhook**: Automatically points to **your n8n server**

**⚡ Quick Setup:**
```bash
# 1. On your local machine:
cd legal-assistant-n8n
./setup-self-hosted.sh

# 2. In your n8n web interface:
# - Import legal-assistant-bot-workflow.json
# - Configure credentials (Telegram, Supabase, Groq)
# - Activate workflow
```

📖 **See [SETUP_FLOW.md](SETUP_FLOW.md) for visual diagram**
📖 **See [SELF_HOSTED_SETUP.md](SELF_HOSTED_SETUP.md) for detailed instructions**

**🌐 IMPORTANT**: Your n8n server must be internet-accessible for Telegram webhooks!

---

### 🐳 **For Docker/New n8n Setup**

If you need to set up n8n from scratch:

### 1. Prerequisites

- Self-hosted n8n instance (already running ✅)
- Telegram Bot Token (from @BotFather)
- Supabase account (free tier)
- Groq API key (free tier - excellent performance)

### 2. Setup Supabase Database

1. Create a new Supabase project
2. Run the SQL from `create-correct-vector-function.sql` in the Supabase SQL editor
   - This creates the table schema, vector search function, and indexes
   - Includes pgvector extension setup and proper permissions
3. Note your project URL and service role key

**Important**: Use only `create-correct-vector-function.sql` - this contains the complete setup that matches your n8n workflow and PDF processing scripts.

### 3. Import Workflow

1. Access your n8n instance
2. Click **"Import from File"**
3. Select `legal-assistant-bot-workflow.json`
4. The workflow will be imported with all nodes configured

### 4. Configure Credentials in n8n

Set up these credential types in your n8n instance:

#### **Telegram Bot API:**
- Credential Type: `Telegram`
- Access Token: `your_telegram_bot_token` (from @BotFather)

#### **Supabase API:**
- Credential Type: `Supabase`
- Host: `https://your-project.supabase.co`
- Service Role Secret: `your_supabase_service_role_key`

#### **HuggingFace API (Vector Search):**
- Credential Type: `HTTP Bearer Auth`
- Token: `your_huggingface_api_token`
- Model: `BAAI/bge-small-en-v1.5` (384-dimensional embeddings)

#### **Groq API:**
- Credential Type: `HTTP Header Auth`
- Header Name: `Authorization`
- Header Value: `Bearer YOUR_GROQ_API_KEY_HERE`

**Note**: Replace placeholder API keys in the workflow JSON with your actual credentials.

### 5. Set Telegram Webhook

Update the webhook URL to point to your n8n instance:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-n8n-domain.com/webhook/telegram-webhook"}'
```

### 6. Activate Workflow

1. In your n8n interface, open the imported workflow
2. Click **"Activate"** to enable the workflow
3. Test by sending a message to your Telegram bot
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-domain.com/webhook/telegram-webhook"}'
```

## Workflow Components

### 1. Telegram Integration
- **Webhook Trigger**: Receives messages from Telegram
- **Voice Processing**: Transcribes voice messages to text
- **Message Normalization**: Standardizes input format

### 2. Content Validation
- **AI Guardrails**: Validates if message is legal/crime related
- **Rejection Handling**: Logs and responds to invalid requests
- **Topic Classification**: Uses Groq models for fast classification

### 3. AI Processing
- **Vector Search**: HuggingFace embeddings for semantic document retrieval
- **Context Preparation**: Combines message, history, and vector-searched legal documents
- **Legal Analysis**: AI-powered analysis using legal knowledge base + RAG
- **Response Formatting**: Structures output (Summary + Breakdown + Conclusion)

### 4. Memory Management
- **Conversation History**: Stores user interactions
- **Context Retrieval**: Maintains conversation continuity
- **Memory Updates**: Updates after each interaction

### 5. Database Operations
- **Rejection Logging**: Tracks invalid requests
- **Document Retrieval**: Accesses legal documents and APIs
- **User Management**: Manages conversation state

## Database Schema

### Tables

1. **legal_documents_vectors**: Vector embeddings for semantic search
   - Schema: `id`, `content`, `embedding (384-dim)`, `metadata`
   - Optimized HNSW indexes for fast similarity search
   - Uses BAAI/bge-small-en-v1.5 embeddings

### Key Features

- pgvector extension with 384-dimensional embeddings
- HNSW indexing for optimized vector similarity search  
- Semantic similarity using cosine distance matching
- Complete schema managed by `create-correct-vector-function.sql`
- Function: `match_legal_documents` for n8n workflow integration

## Free AI Models Configuration

### Groq (Primary - Recommended)
- **Classification**: `llama-3.3-70b-versatile` (fast, accurate content validation)
- **Analysis**: `llama-3.3-70b-versatile` (comprehensive legal analysis)
- **Voice**: `whisper-large-v3` (best transcription quality)

### HuggingFace (Vector Search)
- **Embeddings**: `BAAI/bge-small-en-v1.5` (384-dimensional semantic embeddings)
- **Free Tier**: Generous limits for embedding generation
- **Performance**: Fast and accurate for legal document retrieval

### Alternative Free Options
- **OpenAI**: GPT-3.5-turbo and Whisper (limited free tier)
- **Hugging Face**: Various models (backup option)
- **Google AI Studio**: Gemini API (free tier)

## Legal Document Management

### Supported Formats
- PDF documents (stored in Supabase Storage with vector embeddings)
- Structured text content in database
- External API integrations
- **Vector chunks**: Optimized document segmentation for semantic search

### Document Types
- Constitutional amendments
- Federal and state statutes
- Case law and court decisions
- Regulations and guidelines

### External APIs
- **Free Law Project**: Court opinions and statutes
- **Open States**: State legislature information
- **Justia**: Legal resources and cases

## Vector Search Implementation

### Architecture
The bot uses **HuggingFace BAAI/bge-small-en-v1.5** for generating 384-dimensional embeddings of legal queries and documents. This enables semantic search through the legal document database using cosine similarity.

### Key Components
- **Embedding Generation**: Real-time query embedding via HuggingFace API
- **Document Processing**: PDF documents chunked and embedded using `process-pdfs-from-storage-idempotent.py`
- **Similarity Search**: PostgreSQL with pgvector extension for efficient vector operations
- **RAG Integration**: Retrieved documents enhance AI responses with relevant context

### PDF Processing Scripts

#### **process-pdfs-from-storage-idempotent.py** (Recommended)
- ✅ **Complete processing**: Processes all 46 PDF files from Supabase storage
- ✅ **Idempotent processing**: Safely re-runnable without duplicates
- ✅ **BAAI/bge-small-en-v1.5**: Correct embedding model matching n8n workflow
- ✅ **384-dimensional vectors**: Matches database schema and search function
- ✅ **Error handling**: Robust processing with proper logging and file-based logging
- ✅ **Chunk optimization**: Improved text segmentation for better retrieval
- ✅ **Batch processing**: Efficient database operations with 50-record batches

**Usage:**
```bash
# Process all PDFs and generate embeddings
python process-pdfs-from-storage-idempotent.py

# Monitor progress
tail -f pdf_processing.log
```

**Note**: This script handles all embedding generation and regeneration needs. No additional migration tools are required.

### Database Schema
```sql
-- Vector table for 384-dimensional embeddings
CREATE TABLE legal_documents_vectors (
    id BIGSERIAL PRIMARY KEY,
    document_id UUID REFERENCES legal_documents(id),
    chunk_text TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}'
);

-- Similarity search function
CREATE FUNCTION match_legal_documents(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.3,
    match_count int DEFAULT 5
) RETURNS TABLE (...)
```

### Performance Optimizations
- **HNSW Indexes**: Approximate nearest neighbor search for fast retrieval
- **Chunked Processing**: Documents split into optimal-sized segments
- **Configurable Thresholds**: Similarity matching tuned for legal content
- **Batch Processing**: Efficient embedding generation for document ingestion

### Database Setup
- **`create-correct-vector-function.sql`**: Complete database setup with table schema, vector search function, indexes, and permissions

## Response Format

The bot provides structured responses:

```
**SHORT SUMMARY:**
Brief overview of relevant laws/statutes

**DETAILED BREAKDOWN:**
• Statute/Law 1: Explanation and relevance
• Statute/Law 2: Explanation and relevance
• Case precedent: How it applies

**CONCLUSION:**
Summary of findings and recommended next steps
```

## Security Features

- **Rate Limiting**: Prevents spam and abuse
- **User Authentication**: Basic auth for n8n access
- **Data Encryption**: Encrypted storage of sensitive data
- **Input Validation**: Sanitizes user input
- **HTTPS**: Secure communication (with nginx setup)

## Monitoring and Logging

### Available Logs
- Request/response logs
- Error tracking
- Performance metrics
- User interaction analytics

### Health Checks
- Database connectivity
- API availability
- Webhook status
- Memory usage

## Troubleshooting

### Common Issues

1. **Webhook not receiving messages**
   - Check Telegram webhook URL
   - Verify HTTPS certificate
   - Check firewall settings

2. **AI model not responding**
   - Verify API tokens
   - Check rate limits
   - Monitor API status

3. **Database connection errors**
   - Verify Supabase credentials
   - Check network connectivity
   - Review RLS policies

### Debug Commands

```bash
# Test webhook endpoint
curl -X POST https://your-n8n-domain.com/webhook/telegram-webhook

# Check if Telegram webhook is set correctly
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"

# Test Supabase connection
curl -H "Authorization: Bearer YOUR_SUPABASE_SERVICE_ROLE_KEY" \
     "https://your-project.supabase.co/rest/v1/rejected_requests?select=*&limit=1"

# Test Groq API
curl -H "Authorization: Bearer YOUR_GROQ_API_KEY" \
     "https://api.groq.com/openai/v1/models"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review n8n documentation
3. Create an issue in the repository
4. Contact the development team

## 🎯 Bot Capabilities

Your legal assistant bot handles both **direct legal questions** and **criminal scenario analysis**:

### **📖 Direct Legal Questions:**
- "What are Miranda rights?"
- "How does probable cause work?"
- "What is the difference between burglary and robbery?"
- "What are the elements of assault?"

### **🎭 Criminal Scenario Analysis:**
- "A wife smashes her husband's phone" → Analyzes potential charges (criminal mischief, domestic violence), penalties, defenses
- "Someone took my bike without asking" → Theft analysis, statute elements, potential defenses
- "Two people got in a fight at a bar" → Assault/battery charges, self-defense claims, witness issues
- "My boss made me work off the clock" → Wage theft, labor law violations, civil remedies

### **🔍 What the Bot Provides:**
- **Multiple charge analysis** (identifies ALL potential violations)
- **Statute breakdowns** (specific laws and elements)
- **Case precedents** (relevant court decisions)
- **Defense strategies** (possible legal arguments)
- **Practical outcomes** (likely penalties and next steps)
- **Jurisdictional differences** (federal vs state variations)

📖 **See [SCENARIO_ANALYSIS_EXAMPLES.md](SCENARIO_ANALYSIS_EXAMPLES.md) for detailed examples!**

---

## Additional Documentation

### **📚 User Guides:**
- **[GROQ_BENEFITS.md](GROQ_BENEFITS.md)** - Why we use Groq AI (performance, cost, reliability)
- **[ADVANCED_CUSTOMIZATION.md](ADVANCED_CUSTOMIZATION.md)** - Advanced configuration and customization options
- **[CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md)** - Detailed credential setup instructions
- **[SELF_HOSTED_SETUP.md](SELF_HOSTED_SETUP.md)** - Complete self-hosted installation guide
- **[PDF_VECTOR_INTEGRATION_GUIDE.md](PDF_VECTOR_INTEGRATION_GUIDE.md)** - PDF processing and vector search setup
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

### **⚙️ For Developers:**
- **[ADVANCED_CUSTOMIZATION.md](ADVANCED_CUSTOMIZATION.md)** - JavaScript code examples, API integrations, custom modifications
- **[SETUP_FLOW.md](SETUP_FLOW.md)** - Visual setup process diagram

### **🛠️ Helper Scripts:**
- **[remove-duplicates.sql](remove-duplicates.sql)** - Database maintenance script to clean up duplicate vector entries (not part of main workflow)

---

## Roadmap

- [x] **Vector Search**: Semantic document retrieval with HuggingFace embeddings
- [x] **RAG Integration**: Context-aware responses using retrieved documents
- [x] **Advanced PDF Processing**: Document chunking and embedding pipeline
- [ ] Multi-language support
- [ ] Advanced legal research capabilities
- [ ] Integration with more legal APIs
- [ ] Mobile app interface
- [ ] Advanced analytics dashboard

## Recent Updates

### Vector Search Enhancement (Latest)
- **Upgraded to HuggingFace embeddings** (BAAI/bge-small-en-v1.5)
- **384-dimensional vectors** for optimized performance
- **Improved semantic search** with configurable similarity thresholds
- **Database migration tools** for easy schema updates
- **Enhanced RAG pipeline** for better legal context retrieval