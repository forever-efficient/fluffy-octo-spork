#!/bin/bash

# Legal Assistant n8n Bot Setup Script (Self-Hosted n8n)
# 
# IMPORTANT: Run this script on YOUR LOCAL MACHINE (where you downloaded the files)
# This script will:
# 1. Collect your API credentials
# 2. Test API connections  
# 3. Configure Telegram webhook to point to YOUR n8n server
# 4. Generate setup instructions for importing the workflow
#
# Your n8n server must be internet-accessible for Telegram webhooks to work!

set -e

echo "🏛️  Legal Assistant n8n Bot Setup (Self-Hosted)"
echo "==============================================="
echo ""
echo "📍 Running on: $(hostname) (your local machine)"
echo "🎯 Target: Your self-hosted n8n instance"
echo ""

# Check if required tools are installed
check_requirements() {
    echo "📋 Checking requirements..."
    
    if ! command -v curl &> /dev/null; then
        echo "❌ curl is not installed. Please install curl first."
        exit 1
    fi
    
    echo "✅ Requirements check passed"
}

# Setup Supabase database
setup_database() {
    echo "🗄️  Database setup instructions:"
    echo ""
    echo "1. Go to your Supabase project dashboard"
    echo "2. Navigate to the SQL Editor"
    echo "3. Copy and paste the contents of 'database-schema.sql'"
    echo "4. Run the SQL script to create tables and seed data"
    echo ""
    echo "Press Enter when you've set up the database..."
    read -r
}

# Get API credentials
collect_credentials() {
    echo "🔑 Let's collect your API credentials..."
    echo ""
    
    read -p "Enter your Telegram Bot Token (from @BotFather): " BOT_TOKEN
    read -p "Enter your Supabase URL (https://xxx.supabase.co): " SUPABASE_URL
    read -p "Enter your Supabase Service Role Key: " SUPABASE_KEY
    read -p "Enter your Groq API Key: " GROQ_KEY
    
    echo ""
    echo "🌐 n8n Server Configuration:"
    echo "Your n8n server MUST be accessible from the internet for webhooks to work!"
    echo ""
    echo "Examples of valid URLs:"
    echo "  ✅ https://n8n.yourdomain.com"
    echo "  ✅ https://123.45.67.89:5678 (if you have SSL)"
    echo "  ⚠️  http://123.45.67.89:5678 (works but not secure)"
    echo ""
    echo "Examples that WON'T work:"
    echo "  ❌ http://localhost:5678"
    echo "  ❌ http://192.168.1.100:5678 (private IP)"
    echo ""
    read -p "Enter your n8n server URL (must be internet-accessible): " N8N_URL
    
    # Validate N8N_URL format
    if [[ ! "$N8N_URL" =~ ^https?:// ]]; then
        echo "⚠️  Warning: URL should start with http:// or https://"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Exiting. Please run the script again with a valid URL."
            exit 1
        fi
    fi
    
    echo ""
    echo "✅ Credentials collected!"
}

# Configure Telegram webhook
setup_telegram_webhook() {
    echo ""
    echo "🤖 Setting up Telegram Webhook..."
    
    WEBHOOK_URL="$N8N_URL/webhook/telegram-webhook"
    
    echo "Setting webhook to: $WEBHOOK_URL"
    
    RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$WEBHOOK_URL\"}")
    
    echo "Telegram API Response: $RESPONSE"
    
    # Check if webhook was set successfully
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        echo "✅ Webhook set successfully!"
    else
        echo "❌ Failed to set webhook. Please check your bot token and URL."
    fi
}

# Test API connections
test_apis() {
    echo ""
    echo "🧪 Testing API Connections..."
    echo ""
    
    # Test Groq API
    echo "Testing Groq API..."
    GROQ_RESPONSE=$(curl -s -H "Authorization: Bearer $GROQ_KEY" \
        "https://api.groq.com/openai/v1/models")
    
    if echo "$GROQ_RESPONSE" | grep -q '"object":"list"'; then
        echo "✅ Groq API connection successful"
    else
        echo "❌ Groq API connection failed"
        echo "Response: $GROQ_RESPONSE"
    fi
    
    # Test Supabase API
    echo "Testing Supabase API..."
    SUPABASE_RESPONSE=$(curl -s -H "Authorization: Bearer $SUPABASE_KEY" \
        -H "apikey: $SUPABASE_KEY" \
        "$SUPABASE_URL/rest/v1/")
    
    if [ $? -eq 0 ]; then
        echo "✅ Supabase API connection successful"
    else
        echo "❌ Supabase API connection failed"
    fi
    
    # Test Telegram Bot
    echo "Testing Telegram Bot API..."
    TELEGRAM_RESPONSE=$(curl -s "https://api.telegram.org/bot$BOT_TOKEN/getMe")
    
    if echo "$TELEGRAM_RESPONSE" | grep -q '"ok":true'; then
        echo "✅ Telegram Bot API connection successful"
        BOT_USERNAME=$(echo "$TELEGRAM_RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
        echo "   Bot username: @$BOT_USERNAME"
    else
        echo "❌ Telegram Bot API connection failed"
    fi
}

# Import workflow instructions
workflow_import_instructions() {
    echo ""
    echo "📥 n8n Workflow Import Instructions"
    echo "=================================="
    echo ""
    echo "1. Open your n8n instance in a web browser"
    echo "2. Click 'Add workflow' → 'Import from File'"
    echo "3. Select the 'legal-assistant-bot-workflow.json' file"
    echo "4. Configure the following credentials:"
    echo ""
    echo "   📱 Telegram Bot API:"
    echo "      - Credential Type: Telegram"
    echo "      - Access Token: $BOT_TOKEN"
    echo ""
    echo "   🗄️  Supabase API:"
    echo "      - Credential Type: Supabase"
    echo "      - Host: $SUPABASE_URL"
    echo "      - Service Role Secret: $SUPABASE_KEY"
    echo ""
    echo "   🧠 Groq API:"
    echo "      - Credential Type: HTTP Header Auth"
    echo "      - Header Name: Authorization"
    echo "      - Header Value: Bearer $GROQ_KEY"
    echo ""
    echo "5. Click 'Activate' to enable the workflow"
    echo ""
    echo "Press Enter when you've imported and activated the workflow..."
    read -r
}

# Test the setup
test_bot() {
    echo ""
    echo "🧪 Testing Your Bot"
    echo "=================="
    echo ""
    echo "📱 To test your bot:"
    echo "1. Open Telegram and find your bot: @$BOT_USERNAME"
    echo "2. Send a legal question like: 'What are the Miranda rights?'"
    echo "3. Try a voice message with a legal question"
    echo "4. Test an invalid message like: 'What's the weather?'"
    echo ""
    echo "Expected behavior:"
    echo "✅ Legal questions → Detailed analysis with statutes and cases"
    echo "✅ Voice messages → Transcribed and processed"
    echo "❌ Non-legal questions → Polite rejection with reason"
}

# Create summary file
create_summary() {
    echo ""
    echo "📄 Creating setup summary..."
    
    cat > setup-summary.txt << EOF
🏛️ Legal Assistant Bot - Setup Summary
=====================================

🤖 Telegram Bot: @$BOT_USERNAME
📞 Webhook URL: $N8N_URL/webhook/telegram-webhook
🗄️ Database: $SUPABASE_URL
🧠 AI Provider: Groq (llama3 models)

📋 Credentials Used:
- Telegram Bot Token: $BOT_TOKEN
- Supabase URL: $SUPABASE_URL
- Supabase Service Key: ${SUPABASE_KEY:0:20}...
- Groq API Key: ${GROQ_KEY:0:20}...

🔧 Next Steps:
1. Import legal-assistant-bot-workflow.json into n8n
2. Configure the 3 credential types
3. Activate the workflow
4. Test with legal questions

📚 Documentation:
- README.md - Full documentation
- SELF_HOSTED_SETUP.md - Detailed setup guide
- GROQ_BENEFITS.md - Why we use Groq
- database-schema.sql - Database setup

🆘 Support:
- Check n8n execution logs for errors
- Verify webhook with: curl -X GET "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
- Test APIs with provided curl commands

Setup completed: $(date)
EOF
    
    echo "✅ Setup summary saved to 'setup-summary.txt'"
}

# Cleanup function
cleanup_on_exit() {
    echo ""
    echo "🧹 Setup script completed"
}

# Trap cleanup on exit
trap cleanup_on_exit EXIT

# Main setup flow
main() {
    echo "Starting Legal Assistant Bot setup for self-hosted n8n..."
    echo ""
    
    check_requirements
    setup_database
    collect_credentials
    setup_telegram_webhook
    test_apis
    workflow_import_instructions
    test_bot
    create_summary
    
    echo ""
    echo "🎉 Setup Complete!"
    echo "=================="
    echo ""
    echo "Your Legal Assistant Bot is ready to import into n8n!"
    echo ""
    echo "📁 Key Files:"
    echo "   - legal-assistant-bot-workflow.json (import this)"
    echo "   - SELF_HOSTED_SETUP.md (detailed guide)"
    echo "   - setup-summary.txt (your configuration)"
    echo ""
    echo "🚀 Next: Import the workflow into your n8n instance and activate it!"
    echo ""
    echo "📖 For troubleshooting, see SELF_HOSTED_SETUP.md"
}

# Run main function
main "$@"