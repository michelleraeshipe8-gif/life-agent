"""
Agent Core - Main agent orchestration
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from core.ai_brain import AIBrain
from core.plugin_manager import PluginManager
from core.browser import browser
from core.database import get_db, get_or_create_user
from core.models import Conversation, Memory
import os

logger = logging.getLogger(__name__)


class AgentCore:
    """Main agent orchestration and coordination"""
    
    def __init__(self):
        self.ai_brain = AIBrain()
        self.plugin_manager = PluginManager(self)
        self.browser = browser
        self.current_user_id = None
        self.current_user = None
        self.conversation_context = {}
        
        # Settings
        self.enable_browser = os.getenv('ENABLE_BROWSER_AUTOMATION', 'true').lower() == 'true'
        self.max_context_messages = int(os.getenv('MAX_MEMORY_MESSAGES', '100'))
    
    async def initialize(self):
        """Initialize agent and all components"""
        logger.info("Initializing Agent Core...")
        
        # Initialize database
        from core.database import init_db
        init_db()
        
        # Load plugins
        await self.plugin_manager.load_plugins()
        
        # Initialize browser if enabled
        if self.enable_browser:
            try:
                await self.browser.initialize()
                logger.info("Browser automation enabled")
            except Exception as e:
                logger.warning(f"Browser initialization failed: {e}")
                self.enable_browser = False
        
        logger.info("[OK] Agent Core initialized")
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Agent Core...")
        
        await self.plugin_manager.shutdown_all()
        
        if self.enable_browser:
            await self.browser.shutdown()
        
        logger.info("[OK] Agent Core shutdown complete")
    
    def set_user(self, telegram_id: str, username: str = None, 
                 first_name: str = None, last_name: str = None):
        """Set current user context"""
        user = get_or_create_user(telegram_id, username, first_name, last_name)
        self.current_user_id = user['id']
        self.current_user = user
        
        # Load recent conversation history for context
        self._load_conversation_context()
    
    def _load_conversation_context(self):
        """Load recent conversation history"""
        with get_db() as db:
            recent_convos = db.query(Conversation).filter(
                Conversation.user_id == self.current_user_id
            ).order_by(
                Conversation.timestamp.desc()
            ).limit(self.max_context_messages).all()
            
            # Build context history
            self.conversation_context = {
                'user': self.current_user,
                'history': [
                    {
                        'role': 'user',
                        'content': conv.message,
                        'timestamp': conv.timestamp
                    }
                    for conv in reversed(recent_convos)
                ] + [
                    {
                        'role': 'assistant',
                        'content': conv.response,
                        'timestamp': conv.timestamp
                    }
                    for conv in reversed(recent_convos)
                ]
            }
    
    async def process_message(self, message: str) -> str:
        """
        Main message processing pipeline
        
        Args:
            message: User message
            
        Returns:
            Agent response
        """
        if not self.current_user_id:
            return "Please set user context first"
        
        logger.info(f"Processing message from user {self.current_user_id}: {message[:50]}...")
        
        try:
            # 1. Analyze intent
            intent = await self.ai_brain.analyze_intent(message)
            logger.debug(f"Intent: {intent}")
            
            # 2. Try plugins first
            plugin_response = await self.plugin_manager.route_message(
                message, 
                self.conversation_context
            )
            
            if plugin_response:
                response = plugin_response
            else:
                # 3. Fall back to AI brain for general conversation
                available_plugins = list(self.plugin_manager.plugins.keys())
                response = await self.ai_brain.think(
                    message, 
                    self.conversation_context,
                    available_plugins
                )
            
            # 4. Store conversation
            await self._store_conversation(message, response)
            
            # 5. Extract and store important information as memory
            if intent.get('requires_context'):
                await self._extract_memory(message, response)
            
            # 6. Update context
            self._update_context(message, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return "I encountered an error processing that. Please try again."
    
    async def _store_conversation(self, message: str, response: str):
        """Store conversation in database"""
        with get_db() as db:
            conv = Conversation(
                user_id=self.current_user_id,
                message=message,
                response=response,
                timestamp=datetime.utcnow()
            )
            db.add(conv)
            db.commit()
    
    async def _extract_memory(self, message: str, response: str):
        """Extract important information for long-term memory"""
        try:
            # Use AI to determine if this should be remembered
            summary = await self.ai_brain.summarize_conversation([
                {'role': 'user', 'content': message},
                {'role': 'assistant', 'content': response}
            ])
            
            if len(summary) > 20:  # Only store meaningful summaries
                with get_db() as db:
                    memory = Memory(
                        user_id=self.current_user_id,
                        category='general',
                        content=summary,
                        created_at=datetime.utcnow()
                    )
                    db.add(memory)
                    db.commit()
                    logger.debug(f"Stored memory: {summary[:50]}...")
                    
        except Exception as e:
            logger.error(f"Failed to extract memory: {e}")
    
    def _update_context(self, message: str, response: str):
        """Update conversation context"""
        self.conversation_context['history'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.utcnow()
        })
        self.conversation_context['history'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.utcnow()
        })
        
        # Keep only recent messages
        if len(self.conversation_context['history']) > self.max_context_messages * 2:
            self.conversation_context['history'] = self.conversation_context['history'][-self.max_context_messages * 2:]
    
    async def get_help(self) -> str:
        """Get help message with available commands"""
        help_text = "🤖 **Life Agent - Available Commands**\n\n"
        
        # Get commands from all plugins
        all_commands = self.plugin_manager.get_all_commands()
        
        for plugin_name, commands in all_commands.items():
            help_text += f"\n**{plugin_name}:**\n"
            for cmd, desc in commands.items():
                help_text += f"  • `{cmd}` - {desc}\n"
        
        help_text += "\n\n💡 You can also just talk naturally - I'll understand what you need!"
        
        return help_text
    
    async def list_plugins(self) -> str:
        """List all loaded plugins"""
        plugins = self.plugin_manager.list_plugins()
        
        text = "📦 **Loaded Plugins:**\n\n"
        for plugin in plugins:
            status = "[OK]" if plugin['enabled'] else "✗"
            text += f"{status} **{plugin['name']}** (v{plugin['version']})\n"
            text += f"   {plugin['description']}\n\n"
        
        return text
