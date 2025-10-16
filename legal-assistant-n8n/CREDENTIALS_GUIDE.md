# n8n Credential Configuration Guide

## 🔑 Setting Up Credentials for Legal Assistant Bot

### 1. Telegram Bot API

**Steps:**
1. In n8n, go to **Settings** → **Credentials**
2. Click **"Create New Credential"**
3. Select **"Telegram"**
4. Fill in:
   - **Name**: `telegram-bot-credentials`
   - **Access Token**: Your bot token from @BotFather

**Getting Bot Token:**
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Choose bot name and username
4. Copy the API token provided

---

### 2. Supabase API

**Steps:**
1. In n8n, go to **Settings** → **Credentials**
2. Click **"Create New Credential"**
3. Select **"Supabase"**
4. Fill in:
   - **Name**: `supabase-credentials`
   - **Host**: `https://your-project-id.supabase.co`
   - **Service Role Secret**: Your service role key (not anon key!)

**Getting Supabase Credentials:**
1. Go to [supabase.com](https://supabase.com) and create project
2. Go to **Settings** → **API**
3. Copy **Project URL** and **service_role** key
4. Run the SQL from `create-correct-vector-function.sql` in SQL Editor

---

### 3. Groq API

**Option A: HTTP Header Auth (Recommended)**
1. In n8n, go to **Settings** → **Credentials**
2. Click **"Create New Credential"**
3. Select **"HTTP Header Auth"**
4. Fill in:
   - **Name**: `groq-api-credentials`
   - **Header Name**: `Authorization`
   - **Header Value**: `Bearer your_groq_api_key`

**Option B: Generic Credential**
1. Select **"Generic Credential"**
2. Add property:
   - **Name**: `api_key`
   - **Value**: `your_groq_api_key`

**Getting Groq API Key:**
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up/Login
3. Go to **API Keys**
4. Create new API key

---

## 🔧 Assigning Credentials to Nodes

After importing the workflow, you'll need to assign credentials to these nodes:

### **Telegram Nodes:**
- `Telegram Webhook` - No credential needed
- `Get Voice File` - Assign `telegram-bot-credentials`
- `Send Rejection Response` - Assign `telegram-bot-credentials`
- `Send Legal Response` - Assign `telegram-bot-credentials`

### **Supabase Nodes:**
- `Log Rejection` - Assign `supabase-credentials`
- `Get Conversation Memory` - Assign `supabase-credentials`
- `Get Legal Documents` - Assign `supabase-credentials`
- `Update Conversation Memory` - Assign `supabase-credentials`

### **Groq Nodes:**
- `Transcribe Voice (Groq)` - Assign `groq-api-credentials`
- `Validate Content (Groq)` - Assign `groq-api-credentials`
- `AI Legal Analysis (Groq)` - Assign `groq-api-credentials`

---

## ⚠️ Common Issues

### **Groq Credential Not Available**
If "Groq" isn't in the credential list:
- Use **"HTTP Header Auth"** instead
- Set Header Name: `Authorization`
- Set Header Value: `Bearer your_api_key`

### **Supabase Connection Fails**
- Make sure you're using the **service_role** key, not anon key
- Check that RLS policies allow service role access
- Verify the URL format: `https://project-id.supabase.co`

### **Telegram Webhook Issues**
- Ensure your n8n instance is publicly accessible
- Must use HTTPS (Telegram requirement)
- Check firewall/proxy settings

---

## 🧪 Testing Credentials

### Test Telegram:
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

### Test Supabase:
```bash
curl -H "Authorization: Bearer <YOUR_SERVICE_KEY>" \
     "https://your-project.supabase.co/rest/v1/"
```

### Test Groq:
```bash
curl -H "Authorization: Bearer <YOUR_GROQ_KEY>" \
     "https://api.groq.com/openai/v1/models"
```

All should return successful responses if credentials are correct.

---

## 🎯 Quick Checklist

- [ ] Telegram bot created and token obtained
- [ ] Supabase project created and database schema applied
- [ ] Groq API key obtained
- [ ] All 3 credentials created in n8n
- [ ] Credentials assigned to workflow nodes
- [ ] Workflow activated
- [ ] Telegram webhook configured
- [ ] Test message sent to bot

Once all items are checked, your legal assistant bot is ready to use!