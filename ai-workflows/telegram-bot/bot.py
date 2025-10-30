"""
Telegram bot service for AI Workflows.

IMPORTANT: This service is completely DECOUPLED from the core AI app.
- Does NOT access the vector database directly
- Does NOT know about local models or embeddings
- Communicates ONLY via REST API to the app service
- Completely stateless (all state in REST API)
- Can be scaled/restarted independently

This ensures:
1. Telegram bot can be disabled without affecting AI app
2. AI app can be restarted without losing Telegram sessions
3. Clear separation of concerns
4. Easy to add other bot frontends (Discord, Slack, etc.)
"""

import logging
import os
from typing import Optional

try:
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
        ContextTypes,
    )
    HAS_TELEGRAM = True
except ImportError:
    HAS_TELEGRAM = False

import requests

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot that communicates with REST API."""
    
    def __init__(self, token: str, api_url: str):
        """
        Initialize Telegram bot.
        
        Args:
            token: Telegram bot token from @BotFather
            api_url: Base URL of REST API (e.g., http://app:8000)
        """
        if not HAS_TELEGRAM:
            raise ImportError(
                "python-telegram-bot not installed. "
                "Install with: pip install python-telegram-bot"
            )
        
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.app: Optional[Application] = None
    
    def _build_app(self) -> Application:
        """Build Telegram Application with handlers."""
        app = Application.builder().token(self.token).build()
        
        # Commands
        app.add_handler(CommandHandler("start", self.handle_start))
        app.add_handler(CommandHandler("help", self.handle_help))
        app.add_handler(CommandHandler("health", self.handle_health))
        
        # Messages (queries)
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        return app
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        await update.message.reply_text(
            "🤖 Welcome to AI Workflows!\n\n"
            "Send me any question or document and I'll help you.\n"
            "Use /help for more information."
        )
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        await update.message.reply_text(
            "📖 Available Commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/health - Check API status\n\n"
            "Just send any message and I'll process it using AI."
        )
    
    async def handle_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /health command."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                status_msg = f"✅ API Status: {health.get('status', 'unknown')}\n"
                status_msg += f"🔒 Offline Mode: {health.get('offline_mode')}\n"
                status_msg += f"🦙 Ollama: {'✓' if health.get('ollama_available') else '✗'}"
                await update.message.reply_text(status_msg)
            else:
                await update.message.reply_text("❌ API returned error")
        except requests.exceptions.RequestException as e:
            await update.message.reply_text(f"❌ Cannot reach API: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages."""
        query = update.message.text.strip()
        
        if not query:
            return
        
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        try:
            # Send query to REST API
            response = requests.post(
                f"{self.api_url}/query",
                json={"query": query, "n_results": 5},
                timeout=60,
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "No response")
                
                # Split long responses (Telegram limit is 4096 chars)
                if len(answer) > 4000:
                    # Split into chunks
                    for chunk in [answer[i:i+4000] for i in range(0, len(answer), 4000)]:
                        await update.message.reply_text(chunk)
                else:
                    await update.message.reply_text(answer)
            else:
                await update.message.reply_text(
                    f"❌ API error: {response.status_code}\n{response.text[:200]}"
                )
        except requests.exceptions.Timeout:
            await update.message.reply_text("⏱️ Request timed out. Try a simpler query.")
        except requests.exceptions.RequestException as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:200]}")
    
    def run(self) -> None:
        """Start the Telegram bot."""
        self.app = self._build_app()
        
        logger.info(f"Starting Telegram bot (API: {self.api_url})")
        self.app.run_polling()


async def run_bot_async(token: str, api_url: str) -> None:
    """Run bot asynchronously."""
    bot = TelegramBot(token=token, api_url=api_url)
    app = bot._build_app()
    await app.run_polling()


def main():
    """Main entry point for Telegram bot service."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_url = os.getenv("TELEGRAM_API_URL", "http://localhost:8000")
    
    if not token:
        logger.error(
            "TELEGRAM_BOT_TOKEN not set. "
            "Get token from @BotFather on Telegram."
        )
        return
    
    bot = TelegramBot(token=token, api_url=api_url)
    bot.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
