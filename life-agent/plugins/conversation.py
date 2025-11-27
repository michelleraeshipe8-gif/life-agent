"""
Conversation Plugin - Handle general conversation and queries
"""
from core.plugin import Plugin
from typing import Dict, Any, Optional


class ConversationPlugin(Plugin):
    """Handle general conversation when no other plugin matches"""
    
    name = "Conversation"
    description = "General conversation and knowledge queries"
    version = "1.0.0"
    priority = 999  # Lowest priority - catches everything else
    
    # No keywords - this is the fallback plugin
    keywords = []
    
    async def initialize(self):
        """Initialize plugin"""
        self.logger.info(f"{self.name} initialized (fallback handler)")
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """Always returns True - this is the fallback"""
        return True
    
    async def handle(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Handle general conversation"""
        try:
            # Use AI brain for natural conversation
            response = await self.agent.ai_brain.think(
                message,
                context,
                available_plugins=list(self.agent.plugin_manager.plugins.keys())
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Conversation error: {e}")
            return "I'm having trouble processing that right now. Could you try rephrasing?"
    
    def get_commands(self) -> Dict[str, str]:
        """Get available commands"""
        return {
            "anything!": "I can handle general conversation and questions"
        }
