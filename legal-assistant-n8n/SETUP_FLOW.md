# Setup Flow Diagram

## 📍 Where Everything Runs

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Your Computer  │    │   Your n8n       │    │   Cloud APIs    │
│  (Local)        │    │   Server         │    │                 │
│                 │    │                  │    │                 │
│ 1. Download     │    │ 3. Import        │    │ 2. Create       │
│    files        │    │    workflow      │    │    accounts     │
│                 │    │                  │    │                 │
│ 4. Run          │    │ 5. Configure     │    │ • Telegram      │
│    setup-       │    │    credentials   │    │ • Supabase      │
│    self-        │    │                  │    │ • Groq          │
│    hosted.sh    │    │ 6. Activate      │    │                 │
│                 │    │    workflow      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                              Webhooks
                          (Telegram → n8n)
```

## 🔄 Step-by-Step Process

### Phase 1: Preparation (Your Computer)
1. **Download/clone** this repository to your computer
2. **Create accounts** and get API keys:
   - Telegram: Create bot with @BotFather
   - Supabase: Create project, get URL + service key
   - Groq: Sign up, get API key

### Phase 2: Configuration (Your Computer)
3. **Run setup script** from your computer:
   ```bash
   cd legal-assistant-n8n
   ./setup-self-hosted.sh
   ```
   - Script tests API connections
   - Sets up Telegram webhook pointing to YOUR n8n server
   - Generates configuration summary

### Phase 3: Import (Your n8n Server)
4. **Access your n8n web interface** (browser)
5. **Import workflow** (`legal-assistant-workflow.json`)
6. **Configure credentials** in n8n interface
7. **Activate workflow**

### Phase 4: Database (Supabase Web Interface)
8. **Run SQL script** in Supabase SQL Editor
9. **Test bot** by messaging on Telegram

## 🌐 Network Flow

```
Telegram User → Telegram Servers → Your n8n Server → Groq/Supabase APIs
                                   │
                                   └─→ Response back to user
```

## ❓ Common Questions

**Q: Where do I run the setup script?**
A: On your local computer/laptop where you downloaded these files.

**Q: Where is the webhook configured?**
A: The setup script configures Telegram to send webhooks to your n8n server URL.

**Q: What if my n8n is on a private network?**
A: Use ngrok or similar tunnel: `ngrok http 5678` to expose it temporarily.

**Q: Can I run this on the same server as n8n?**
A: Yes, but you still need the n8n server to be internet-accessible for webhooks.

**Q: Do I need to install anything on the n8n server?**
A: No! Just import the workflow file through the web interface.

## 🚨 Requirements Checklist

- [ ] n8n server is running and accessible via web browser
- [ ] n8n server has internet access (can reach external APIs)
- [ ] n8n server is reachable from internet (for Telegram webhooks)
- [ ] You have admin access to n8n interface
- [ ] You can run scripts on your local computer