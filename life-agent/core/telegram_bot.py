"""
Telegram Bot Interface
"""
import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from core.agent_core import AgentCore

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot interface for the agent"""
    
    def __init__(self, agent_core: AgentCore):
        self.agent = agent_core
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        
        self.app = Application.builder().token(self.token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup message and command handlers"""
        # Commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("plugins", self.plugins_command))
        
        # Message handler (for everything else)
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))
        
        # Photo handler
        self.app.add_handler(MessageHandler(
            filters.PHOTO,
            self.handle_photo
        ))
        
        # Voice handler
        self.app.add_handler(MessageHandler(
            filters.VOICE,
            self.handle_voice
        ))
        
        # Document handler
        self.app.add_handler(MessageHandler(
            filters.Document.ALL,
            self.handle_document
        ))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Set user context in agent
        self.agent.set_user(
            str(user.id),
            user.username,
            user.first_name,
            user.last_name
        )
        
        welcome_message = f"""👋 Hey {user.first_name}!

I'm your personal life assistant. I can help you with:

• 💭 Remember important information
• ⏰ Set smart reminders
• 📅 Manage your calendar
• 💰 Track finances
• 👥 Manage relationships
• And much more!

Just talk to me naturally - I'll understand what you need.

Try asking me something like:
• "Remind me to call mom tomorrow at 2pm"
• "How much did I spend on food this month?"
• "What's on my calendar today?"

Type /help to see all available commands."""
        
        await update.message.reply_text(welcome_message)
        logger.info(f"New user started: {user.id} ({user.username})")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = await self.agent.get_help()
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def plugins_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /plugins command"""
        plugins_text = await self.agent.list_plugins()
        await update.message.reply_text(plugins_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user = update.effective_user
        message = update.message.text
        
        # Set user context
        self.agent.set_user(
            str(user.id),
            user.username,
            user.first_name,
            user.last_name
        )
        
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        # Process message
        response = await self.agent.process_message(message)
        
        # Send response
        await update.message.reply_text(response)
        
        logger.info(f"User {user.id}: {message[:30]}... -> Response sent")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages"""
        user = update.effective_user
        self.agent.set_user(
            str(user.id),
            user.username,
            user.first_name,
            user.last_name
        )
        
        # Download photo
        photo_file = await update.message.photo[-1].get_file()
        photo_path = f"data/uploads/{user.id}_{photo_file.file_id}.jpg"
        await photo_file.download_to_drive(photo_path)
        
        caption = update.message.caption or "Photo received"
        
        # Process with context about photo
        message = f"[Photo uploaded: {photo_path}] {caption}"
        response = await self.agent.process_message(message)
        
        await update.message.reply_text(response)
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages"""
        user = update.effective_user
        self.agent.set_user(
            str(user.id),
            user.username,
            user.first_name,
            user.last_name
        )
        
        # Download voice message
        voice_file = await update.message.voice.get_file()
        voice_path = f"data/uploads/{user.id}_{voice_file.file_id}.ogg"
        await voice_file.download_to_drive(voice_path)
        
        # TODO: Transcribe with Whisper if voice plugin enabled
        response = "Voice message received. (Voice transcription coming soon!)"
        
        await update.message.reply_text(response)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        user = update.effective_user
        self.agent.set_user(
            str(user.id),
            user.username,
            user.first_name,
            user.last_name
        )
        
        # Download document
        doc_file = await update.message.document.get_file()
        doc_path = f"data/uploads/{user.id}_{update.message.document.file_name}"
        await doc_file.download_to_drive(doc_path)
        
        message = f"[Document uploaded: {doc_path}] {update.message.caption or ''}"
        response = await self.agent.process_message(message)
        
        await update.message.reply_text(response)
    
    async def run(self):
        """Start the bot"""
        logger.info("Starting Telegram bot...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        logger.info("[OK] Telegram bot running")
    
    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping Telegram bot...")
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        logger.info("[OK] Telegram bot stopped")
