# fluffy-octo-spork

## Legal Assistant n8n Bot with Vector Search

A comprehensive OSINT toolkit featuring an advanced Telegram legal assistant bot built with n8n automation platform. The bot provides AI-powered legal analysis with semantic document search capabilities.

### 🎯 Current Focus: Legal Assistant Bot

Located in `/legal-assistant-n8n/`, this project includes:

- **🤖 Telegram Bot**: AI-powered legal and criminal law assistance
- **🔍 Vector Search**: HuggingFace embeddings for semantic document retrieval
- **🧠 RAG Integration**: Context-aware responses using retrieved legal documents
- **📚 PDF Processing**: Automated document chunking and embedding pipeline
- **🛡️ Content Validation**: AI guardrails for legal/crime topics only
- **💾 Conversation Memory**: Persistent context for follow-up questions

### 🆕 Recent Updates

- **Vector Search Implementation**: Upgraded to HuggingFace BAAI/bge-small-en-v1.5 (384-dimensional embeddings)
- **Database Migration**: Complete schema update with migration scripts
- **Performance Optimization**: HNSW indexes and configurable similarity thresholds
- **Enhanced RAG Pipeline**: Improved legal context retrieval and AI responses

### 📁 Repository Structure

```
legal-assistant-n8n/           # Main project - Telegram legal bot
├── legal-assistant-bot-workflow.json    # Complete n8n workflow
├── create-correct-vector-function.sql    # Complete database setup
├── process-pdfs-from-storage-idempotent.py # PDF processing pipeline
└── README.md                            # Detailed setup instructions

docker-ai-n8n.yml             # Docker configuration for n8n
osint-env-helper.sh            # Environment setup helper
osint-kali-playbook.yml        # Ansible playbook for Kali setup
```

### 🚀 Quick Start

```bash
cd legal-assistant-n8n
./setup-self-hosted.sh
```

See `/legal-assistant-n8n/README.md` for complete setup instructions.

### 🔧 Technologies

- **n8n**: Workflow automation platform
- **Supabase**: PostgreSQL database with pgvector extension
- **HuggingFace**: BAAI/bge-small-en-v1.5 embedding model
- **Groq**: Fast AI inference for legal analysis
- **Telegram**: Bot interface for user interactions

### 📖 Documentation

- [Legal Assistant Setup Guide](legal-assistant-n8n/SELF_HOSTED_SETUP.md)
- [Vector Search Implementation](legal-assistant-n8n/README.md#vector-search-implementation)
- [Database Schema Documentation](legal-assistant-n8n/README.md#database-schema)
- [Troubleshooting Guide](legal-assistant-n8n/TROUBLESHOOTING.md)