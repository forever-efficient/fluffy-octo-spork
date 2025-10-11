# Legal Assistant n8n Bot

A comprehensive n8n automation workflow that creates a Telegram bot for legal and criminal law assistance. The bot validates incoming messages, processes legal questions using AI, and maintains conversation memory for follow-up questions.

## Features

- 🤖 **Telegram Integration**: Receives text and voice messages
- 🛡️ **Content Guardrails**: AI-powered validation for legal/crime topics only
- 🎯 **Scenario Analysis**: Analyzes criminal scenarios (e.g., "a wife smashes her husband's phone")
- ❓ **Direct Legal Questions**: Answers specific legal questions (e.g., "What are Miranda rights?")
- 🧠 **AI Legal Analysis**: Uses free AI models for comprehensive legal reasoning
- 📚 **Document Access**: Integrates with legal PDFs and external APIs
- 💾 **Conversation Memory**: Maintains context for follow-up questions
- 📊 **Database Logging**: Tracks rejected requests and conversation history
- 🔒 **Security**: Rate limiting and user management

## Architecture

```
Telegram Message → Content Validation → AI Analysis → Response Formatting → Database Logging
                ↓                   ↓              ↓                    ↓
            Voice-to-Text      Legal Document   Conversation      Rejection
                              Retrieval        Memory Update      Logging
```

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
# - Import legal-assistant-workflow.json
# - Configure 3 credentials
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
2. Run the SQL from `database-schema.sql` in the Supabase SQL editor
3. Note your project URL and service role key

### 3. Import Workflow

1. Access your n8n instance
2. Click **"Import from File"**
3. Select `legal-assistant-workflow.json`
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

#### **Groq API:**
- Credential Type: `HTTP Header Auth` or `Generic Credential`
- Header Name: `Authorization`
- Header Value: `Bearer your_groq_api_key`

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
- **Context Preparation**: Combines message, history, and legal documents
- **Legal Analysis**: AI-powered analysis using legal knowledge base
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

1. **rejected_requests**: Logs invalid messages
2. **user_conversations**: Stores conversation history
3. **legal_documents**: Legal PDFs and document content
4. **legal_apis**: External API configurations

### Key Features

- Row Level Security (RLS) enabled
- Optimized indexes for performance
- JSONB fields for flexible metadata
- Service role access for n8n

## Free AI Models Configuration

### Groq (Primary - Recommended)
- **Classification**: `llama3-8b-8192` (fast, accurate)
- **Analysis**: `llama3-70b-8192` (comprehensive legal analysis)
- **Voice**: `whisper-large-v3` (best transcription quality)

### Alternative Free Options
- **OpenAI**: GPT-3.5-turbo and Whisper (limited free tier)
- **Hugging Face**: Various models (backup option)
- **Google AI Studio**: Gemini API (free tier)

## Legal Document Management

### Supported Formats
- PDF documents (stored in Supabase Storage)
- Structured text content in database
- External API integrations

### Document Types
- Constitutional amendments
- Federal and state statutes
- Case law and court decisions
- Regulations and guidelines

### External APIs
- **Free Law Project**: Court opinions and statutes
- **Open States**: State legislature information
- **Justia**: Legal resources and cases

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

## Roadmap

- [ ] Multi-language support
- [ ] Advanced legal research capabilities
- [ ] Integration with more legal APIs
- [ ] Mobile app interface
- [ ] Advanced analytics dashboard