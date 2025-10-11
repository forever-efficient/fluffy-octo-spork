#!/bin/bash

# Legal Assistant n8n Bot Setup Script
# This script helps you set up the legal assistant bot quickly

set -e

echo "🏛️    echo "3. Configure the following credentials:"
    echo "   - Telegram Bot API"
    echo "   - Supabase API" 
    echo "   - Groq API"gal Assistant n8n Bot Setup"
echo "================================="

# Check if required tools are installed
check_requirements() {
    echo "📋 Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    echo "✅ Requirements check passed"
}

# Generate encryption key
generate_encryption_key() {
    echo "🔐 Generating encryption key..."
    openssl rand -hex 16
}

# Setup environment file
setup_env() {
    echo "⚙️  Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "📄 Created .env file from template"
        
        # Generate encryption key
        ENCRYPTION_KEY=$(generate_encryption_key)
        
        # Update .env file with generated key
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/YOUR_32_CHARACTER_ENCRYPTION_KEY/$ENCRYPTION_KEY/" .env
        else
            # Linux
            sed -i "s/YOUR_32_CHARACTER_ENCRYPTION_KEY/$ENCRYPTION_KEY/" .env
        fi
        
        echo "🔑 Generated encryption key: $ENCRYPTION_KEY"
        
        echo ""
        echo "📝 Please edit the .env file and add your credentials:"
        echo "   - TELEGRAM_BOT_TOKEN (from @BotFather)"
        echo "   - SUPABASE_URL (from your Supabase project)"
        echo "   - SUPABASE_SERVICE_ROLE_KEY (from Supabase)"
        echo "   - GROQ_API_KEY (from Groq Console)"
        echo ""
        echo "Press Enter when you've updated the .env file..."
        read -r
    else
        echo "✅ .env file already exists"
    fi
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

# Start services
start_services() {
    echo "🚀 Starting services..."
    
    # Create necessary directories
    mkdir -p ssl
    
    # Start with docker-compose
    docker-compose up -d
    
    echo "✅ Services started successfully!"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
}

# Configure Telegram webhook
setup_telegram_webhook() {
    echo ""
    echo "🤖 Telegram Webhook Setup"
    echo "========================"
    
    read -p "Enter your Telegram Bot Token: " BOT_TOKEN
    read -p "Enter your webhook URL (e.g., https://your-domain.com/webhook/telegram-webhook): " WEBHOOK_URL
    
    echo "Setting up webhook..."
    
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

# Import n8n workflow
import_workflow() {
    echo ""
    echo "📥 n8n Workflow Import Instructions"
    echo "=================================="
    echo ""
    echo "1. Open your browser and go to http://localhost:5678"
    echo "2. Login with your credentials (check docker-compose.yml)"
    echo "3. Click on 'Import from File'"
    echo "4. Select the 'legal-assistant-workflow.json' file"
    echo "5. Configure the following credentials:"
    echo "   - Telegram Bot API"
    echo "   - Supabase API" 
    echo "   - Hugging Face API"
    echo "6. Activate the workflow"
    echo ""
    echo "Press Enter when you've imported the workflow..."
    read -r
}

# Test the setup
test_setup() {
    echo ""
    echo "🧪 Testing Setup"
    echo "==============="
    
    echo "Testing n8n availability..."
    if curl -s http://localhost:5678 > /dev/null; then
        echo "✅ n8n is accessible at http://localhost:5678"
    else
        echo "❌ n8n is not accessible. Check the logs with: docker-compose logs n8n"
    fi
    
    echo ""
    echo "📱 To test your bot:"
    echo "1. Send a message to your Telegram bot"
    echo "2. Try: 'What are the Miranda rights?'"
    echo "3. Check the n8n execution logs"
}

# Cleanup function
cleanup_on_exit() {
    echo ""
    echo "🧹 Cleanup complete"
}

# Trap cleanup on exit
trap cleanup_on_exit EXIT

# Main setup flow
main() {
    echo "Starting Legal Assistant Bot setup..."
    echo ""
    
    check_requirements
    setup_env
    setup_database
    start_services
    
    echo ""
    echo "🎉 Basic setup complete!"
    echo ""
    
    read -p "Do you want to set up the Telegram webhook now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_telegram_webhook
    fi
    
    echo ""
    import_workflow
    test_setup
    
    echo ""
    echo "🏁 Setup Complete!"
    echo "=================="
    echo ""
    echo "Your Legal Assistant Bot is now ready!"
    echo ""
    echo "📍 Important URLs:"
    echo "   n8n Interface: http://localhost:5678"
    echo "   Webhook URL: https://your-domain.com/webhook/telegram-webhook"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Configure your domain and SSL certificates"
    echo "   2. Update your webhook URL in Telegram"
    echo "   3. Add legal documents to your Supabase database"
    echo "   4. Test the bot with legal questions"
    echo ""
    echo "📖 For more information, see README.md"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "   - Check logs: docker-compose logs -f"
    echo "   - Restart services: docker-compose restart"
    echo "   - Stop services: docker-compose down"
}

# Run main function
main "$@"