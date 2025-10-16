# Troubleshooting: "Has Message Content" Node Hanging

## � **IMMEDIATE FIX - Try This First:**

### **Option 1: Re-import Updated Workflow**
1. **Download the updated** `legal-assistant-bot-workflow.json` 
2. **Delete the hanging workflow** in your n8n
3. **Import the new version** (I've fixed the problematic conditions)
4. **Configure credentials** again
5. **Test** with "what are miranda rights"

### **Option 2: Quick Manual Fix**
1. **Open the hanging workflow** in n8n
2. **Click on "Has Message Content" node**
3. **Change the condition to:**
   - **Value 1**: `{{ $json.message?.text || '' }}`
   - **Operation**: `is not empty`
   - **Value 2**: (leave empty - not needed for "is not empty")
4. **Save and test**

---

## 🔍 **Root Cause Analysis:**

## 🔍 **Debug Test Steps**

If the main workflow still hangs, use these debugging steps to identify the exact issue:

1. **Add a debug Code node** after the Telegram Webhook trigger
2. **Configure** the same Telegram credentials  
3. **Use the debug code** provided below to inspect the data structure
4. **Send a test message** - check n8n execution logs for debug output
5. **Apply fixes** based on the debug information

**Debug Code Node JavaScript:**
```javascript
// Debug webhook data structure
console.log('=== WEBHOOK DEBUG ===');
console.log('Full input data:', JSON.stringify($input.all(), null, 2));
console.log('First item:', JSON.stringify($input.first(), null, 2));
return $input.all();
```

---

## 🔍 **Quick Debugging Steps:**

### **Step 1: Check Webhook Data Structure**

1. **In your n8n workflow**, temporarily add a **"Code" node** right after the Telegram Webhook
2. **Replace the JavaScript** with this debug code:

```javascript
// Debug: Log incoming Telegram data
console.log('Full webhook data:', JSON.stringify($json, null, 2));

// Check message structure
if ($json.message) {
    console.log('Message object exists');
    console.log('Message text:', $json.message.text);
    console.log('Message from:', $json.message.from);
    console.log('Message chat:', $json.message.chat);
} else {
    console.log('No message object found');
    console.log('Available keys:', Object.keys($json));
}

// Return the data unchanged
return [$json];
```

3. **Send a test message** to your bot
4. **Check the n8n execution logs** to see what data structure is actually coming in

### **Step 2: Fix the "Has Message Content" Node**

The issue is likely in the condition logic. **Update the "Has Message Content" node**:

**Current (problematic) condition:**
```
{{ $json.message.text || $json.message.voice || $json.message.audio }}
```

**Fixed condition:**
```javascript
// Option 1: Simple check
{{ $json.message && $json.message.text ? 'true' : 'false' }}

// Option 2: More comprehensive
{{ $json.message && ($json.message.text || $json.message.voice) ? 'true' : 'false' }}
```

**In the n8n interface:**
1. Click on "Has Message Content" node
2. Change **Operation** to "equal"
3. **Value 1**: `{{ $json.message && $json.message.text ? 'true' : 'false' }}`
4. **Value 2**: `true`

### **Step 3: Alternative - Bypass the Check Temporarily**

For immediate testing, you can temporarily **bypass this node**:

1. **Disconnect** the "Has Message Content" node
2. **Connect** "Telegram Webhook" directly to "Is Voice Message"
3. **Test** if the workflow proceeds

### **Step 4: Check Telegram Webhook Format**

Telegram sends different data structures depending on the message type:

**Text Message Structure:**
```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "from": {
      "id": 123456789,
      "is_bot": false,
      "first_name": "John",
      "username": "john_doe"
    },
    "chat": {
      "id": 123456789,
      "first_name": "John",
      "username": "john_doe",
      "type": "private"
    },
    "date": 1234567890,
    "text": "what are miranda rights"
  }
}
```

## 🛠️ **Updated Workflow Fix**

I've updated the workflow file with a more robust condition. **Re-import the workflow** or manually update the "Has Message Content" node with this configuration:

**Node Settings:**
- **Type**: IF
- **Condition Type**: String
- **Value 1**: `={{ $json.message && $json.message.text ? 'true' : 'false' }}`
- **Operation**: equal
- **Value 2**: `true`

## 🧪 **Testing Steps:**

1. **Import the updated workflow** or fix the condition manually
2. **Send a simple text message**: "test"
3. **Check execution logs** in n8n for any errors
4. **Try your original message**: "what are miranda rights"

## 🚨 **Common Issues & Solutions:**

### **Issue 1: Webhook not receiving data**
```bash
# Test if webhook is working at all
curl -X POST "https://your-n8n-domain.com/webhook/telegram-webhook" \
     -H "Content-Type: application/json" \
     -d '{"message":{"text":"test","from":{"id":123},"chat":{"id":123}}}'
```

### **Issue 2: Wrong webhook URL**
```bash
# Check current webhook
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"

# Should show your n8n webhook URL
```

### **Issue 3: n8n not accessible**
- Verify your n8n URL is publicly accessible
- Check firewall/proxy settings
- Test with: `curl https://your-n8n-domain.com`

### **Issue 4: Credential issues**
- Make sure Telegram credentials are properly configured
- Test bot token: `curl "https://api.telegram.org/bot<TOKEN>/getMe"`

## 📝 **Quick Fix Workflow**

If you want to test immediately, here's a minimal test workflow:

1. **Create new workflow** in n8n
2. **Add Telegram Webhook** node
3. **Add Code node** with:
```javascript
// Simple responder
return [{
    json: {
        chatId: $json.message.chat.id,
        text: `You said: ${$json.message.text}`
    }
}];
```
4. **Add Telegram Send Message** node
5. **Test** with a simple message

This will help isolate if the issue is with the complex workflow or basic Telegram integration.

## 🔧 **Next Steps:**

1. Try the debug code to see actual webhook data
2. Update the "Has Message Content" node condition
3. Test with simple messages first
4. Gradually add complexity back

Let me know what the debug output shows and I can help fix the specific issue!

---

## 🆕 **Latest Fixes (Updated)**

### **Fixed Issues:**

#### 1. **Invalid Operation Names**
**Problem:** "isNotEqual" operation doesn't exist in n8n IF nodes
**Solution:** Use "isNotEmpty" instead

```javascript
// ❌ Wrong
"operation": "isNotEqual"

// ✅ Correct  
"operation": "isNotEmpty"
```

#### 2. **Webhook Data Structure with Body Wrapper**
**Problem:** Some Telegram webhooks wrap data in `body` object
**Solution:** Update all JSON paths to handle both structures

```javascript
// ❌ Wrong paths
$json.message.text
$json.message.voice
$json.message.chat.id

// ✅ Correct paths (handles body wrapper)
$json.body.message?.text || $json.message?.text
$json.body.message?.voice || $json.message?.voice  
$json.body.message?.chat?.id || $json.message?.chat?.id
```

#### 3. **Node Connection Issues**
**Problem:** "Normalize Message" node shows "no connectors"
**Solution:** Verify connections from "Is Voice Message" node:
- FALSE branch (index 1) → "Normalize Message"
- TRUE branch (index 0) → "Get Voice File"

#### 4. **Voice Message File Paths**
**Problem:** Voice file references incorrect
**Solution:** Use proper file ID path:
```javascript
// ❌ Wrong
$json.message.voice.file_path

// ✅ Correct
$json.body.message?.voice?.file_id || $json.message?.voice?.file_id
```

### **Quick Test Commands:**

Test webhook structure:
```bash
curl -X POST "https://your-n8n-domain.com/webhook/telegram-webhook" \
     -H "Content-Type: application/json" \
     -d '{"body":{"message":{"text":"test","chat":{"id":123},"from":{"id":456}}}}'
```

Or without body wrapper:
```bash
curl -X POST "https://your-n8n-domain.com/webhook/telegram-webhook" \
     -H "Content-Type: application/json" \
     -d '{"message":{"text":"test","chat":{"id":123},"from":{"id":456}}}'
```