# Self-Hosted n8n Setup Guide for Legal Assistant Bot

## 🚀 Quick Setup (5 Minutes)

### 📍 **Where to Run Everything**

**Setup Script**: Run on **your local machine** (where you downloaded these files)
**Webhook**: Points to **your n8n server** (wherever n8n is hosted)
**Workflow Import**: Done in **your n8n web interface**

### 🔧 **Prerequisites**

- Your n8n instance URL (e.g., `https://n8n.yourdomain.com` or `http://your-server-ip:5678`)
- Access to your n8n web interface
- Terminal/command prompt on your local machine
- **Your n8n server must be internet-accessible** (for Telegram webhooks)

### 🌐 **Network Requirements**

For the bot to work, Telegram needs to send webhooks to your n8n server:

**✅ Works:**
- `https://n8n.yourdomain.com` (public domain with SSL)
- `https://your-public-ip:5678` (public IP with SSL)
- `http://your-public-ip:5678` (public IP - not recommended)

**❌ Won't Work:**
- `http://localhost:5678` (not accessible from internet)
- `http://192.168.1.100:5678` (private IP)
- `http://10.0.0.50:5678` (private IP)

**💡 Solutions if n8n is not public:**
- Use ngrok: `ngrok http 5678` (temporary tunnel)
- Set up reverse proxy with SSL
- Use cloud hosting for n8n

---

## Step 1: Run Setup Script (On Your Local Machine)

From the directory where you downloaded these files:

```bash
cd legal-assistant-n8n
./setup-self-hosted.sh
```

**What this script does:**
- Collects your API credentials
- Tests API connections
- Sets up Telegram webhook (points to your n8n server)
- Generates configuration summary

**You'll be prompted for:**
- Telegram Bot Token
- Supabase URL and Service Key  
- Groq API Key
- **Your n8n server URL** (e.g., `https://n8n.yourdomain.com`)

---

## Step 2: Import Workflow (In Your n8n Web Interface)

## Step 2: Import Workflow (In Your n8n Web Interface)

**Access your n8n interface** (e.g., go to `https://n8n.yourdomain.com` in your browser):

1. Open your n8n instance
2. Click **"+ Add workflow"** → **"Import from file"**
3. Select `legal-assistant-workflow.json` (from your local machine)
4. Click **"Import"**

## Step 3: Configure Credentials (In n8n Interface)

You'll need to set up 3 credential types:

#### 🤖 **Telegram Bot API**
```
Credential Type: Telegram
Name: telegram-bot-credentials
Access Token: [Your bot token from @BotFather]
```

#### 🗄️ **Supabase API**
```
Credential Type: Supabase
Name: supabase-credentials  
Host: https://your-project.supabase.co
Service Role Secret: [Your Supabase service role key]
```

#### 🧠 **Groq API**
```
Credential Type: HTTP Header Auth
Name: groq-api-credentials
Header Name: Authorization
Header Value: Bearer [your_groq_api_key]
```

## Step 4: Set Up Database (In Supabase Web Interface)

**Go to your Supabase project dashboard:**

1. Go to your Supabase project
2. Open **SQL Editor**
3. Copy and paste the contents of `database-schema.sql` (from your local files)
4. Click **"Run"**

## Step 5: Configure Webhook (Automatic - Done by Setup Script)

**This happens automatically when you run the setup script!**

The script will run this command for you:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-n8n-domain.com/webhook/telegram-webhook"}'
```

**The webhook URL points to your n8n server:**
- If n8n is at `https://n8n.yourdomain.com`, webhook will be `https://n8n.yourdomain.com/webhook/telegram-webhook`
- If n8n is at `http://192.168.1.100:5678`, webhook will be `http://192.168.1.100:5678/webhook/telegram-webhook`

⚠️ **Important**: Your n8n server must be accessible from the internet for Telegram to send webhooks!

## Step 6: Activate & Test (In n8n Interface)

1. Click **"Activate"** in the top-right of your workflow
2. Send a test message to your Telegram bot
3. Try: "What are the Miranda rights?"

## 🔧 Credential Configuration Details

### Setting Up Groq Credentials

Since n8n might not have a built-in Groq credential type, use one of these methods:

**Option 1: HTTP Header Auth**
- Type: `HTTP Header Auth`
- Header Name: `Authorization` 
- Header Value: `Bearer your_groq_api_key`

**Option 2: Generic Credential**
- Type: `Generic Credential`
- Add property: `api_key` = `your_groq_api_key`
- Then update nodes to use: `Bearer {{$credentials.groq.api_key}}`

### Telegram Bot Setup

1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions to create bot
4. Copy the API token
5. Set bot commands (optional):
   ```
   /start - Start the legal assistant
   /help - Get help with legal questions
   ```

### Supabase Setup

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Go to **Settings** → **API**
4. Copy:
   - Project URL
   - Service role key (not anon key!)

## 🧪 Testing Your Setup

### Test Individual Components:

**1. Test Webhook:**
```bash
curl -X POST "https://your-n8n-domain.com/webhook/telegram-webhook" \
     -H "Content-Type: application/json" \
     -d '{"message":{"text":"test","from":{"id":123},"chat":{"id":123}}}'
```

**2. Test Supabase:**
- Check if tables were created in Supabase dashboard
- Try inserting a test record

**3. Test Groq:**
```bash
curl -H "Authorization: Bearer YOUR_GROQ_API_KEY" \
     "https://api.groq.com/openai/v1/models"
```

**4. Test Telegram Bot:**
- Find your bot on Telegram
- Send message: "What is probable cause?"
- Should get legal analysis response

## 🔧 Common Issues & Solutions

### **Workflow Import Fails**
- Make sure n8n version supports the workflow format
- Check that file isn't corrupted
- Try importing individual nodes if needed

### **Groq Credential Issues**
- Verify API key is correct
- Check if you need to enable API access in Groq console
- Ensure you're using the correct authentication header

### **Webhook Not Responding**
- Check n8n webhook URL is publicly accessible
- Verify HTTPS (Telegram requires HTTPS)
- Check firewall/proxy settings

### **Database Errors**
- Verify Supabase service role key (not anon key)
- Check RLS policies allow service role access
- Ensure database schema was created correctly

## 🎯 Workflow Nodes Overview

Your imported workflow contains these main nodes:

1. **Telegram Webhook** - Receives messages
2. **Voice Processing** - Handles voice messages  
3. **Content Validation** - Checks if message is legal-related
4. **Database Operations** - Logs and retrieves data
5. **AI Analysis** - Processes legal questions
6. **Response Formatting** - Formats and sends replies

## 📱 Bot Commands

Once active, your bot responds to:

- **Text messages** about legal/criminal matters
- **Voice messages** (automatically transcribed)
- **Follow-up questions** (remembers conversation context)

Invalid requests are logged and politely rejected.

## 🚀 You're Done!

Your legal assistant bot is now ready to help users with:
- Criminal law questions
- Statute explanations  
- Case law analysis
- Legal procedure guidance
- Court ruling interpretations

The bot maintains conversation memory and provides structured responses with legal reasoning and next steps.