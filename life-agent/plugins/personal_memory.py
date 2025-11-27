"""
Personal Memory Plugin - Remember and recall user information
"""
from core.plugin import Plugin
from core.models import Memory
from core.database import get_db
from datetime import datetime
from typing import Dict, Any, Optional
import re


class PersonalMemoryPlugin(Plugin):
    """Stores and retrieves personal information"""
    
    name = "Personal Memory"
    description = "Remembers important information about you and recalls it when needed"
    version = "1.0.0"
    priority = 10
    
    keywords = [
        "remember", "recall", "forget", "what did",
        "when did", "have i", "did i", "my", "i told you"
    ]
    
    async def initialize(self):
        """Initialize plugin"""
        self.logger.info(f"{self.name} initialized")
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """Check if message is about memory"""
        message_lower = message.lower()
        
        # Check for explicit memory commands
        if any(keyword in message_lower for keyword in self.keywords):
            return True
        
        # Check for memory storage phrases
        memory_phrases = [
            "my name is", "i am", "i live", "i work",
            "my favorite", "i like", "i prefer", "i hate"
        ]
        
        if any(phrase in message_lower for phrase in memory_phrases):
            return True
        
        return False
    
    async def handle(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Handle memory-related messages"""
        message_lower = message.lower()
        
        # Check for recall requests
        if any(word in message_lower for word in ["recall", "what", "when", "have i", "did i"]):
            return await self._recall_memory(message)
        
        # Check for forget requests
        if "forget" in message_lower:
            return await self._forget_memory(message)
        
        # Otherwise, store as new memory
        return await self._store_memory(message, context)
    
    async def _store_memory(self, message: str, context: Dict[str, Any]) -> str:
        """Store new memory"""
        try:
            # Extract category from message
            category = self._determine_category(message)
            
            # Store memory
            with get_db() as db:
                memory = Memory(
                    user_id=self.agent.current_user_id,
                    category=category,
                    content=message,
                    importance=0.7,  # Default importance
                    created_at=datetime.utcnow()
                )
                db.add(memory)
                db.commit()
            
            self.logger.info(f"Stored memory: {message[:50]}...")
            return "[OK] Got it, I'll remember that."
            
        except Exception as e:
            self.logger.error(f"Failed to store memory: {e}")
            return "Sorry, I had trouble storing that memory."
    
    async def _recall_memory(self, query: str) -> str:
        """Recall relevant memories"""
        try:
            with get_db() as db:
                # Search memories
                memories = db.query(Memory).filter(
                    Memory.user_id == self.agent.current_user_id
                ).order_by(
                    Memory.importance.desc(),
                    Memory.last_accessed.desc()
                ).limit(10).all()
                
                if not memories:
                    return "I don't have any memories stored yet. Tell me about yourself!"
                
                # Use AI to find relevant memory
                context = {
                    'query': query,
                    'memories': [
                        {'content': m.content, 'category': m.category, 'date': m.created_at}
                        for m in memories
                    ]
                }
                
                # Find best match using AI
                response = await self.agent.ai_brain.think(
                    f"Based on these memories: {context}, answer this query: {query}",
                    {}
                )
                
                # Update access count for used memories
                for memory in memories:
                    memory.last_accessed = datetime.utcnow()
                    memory.access_count += 1
                db.commit()
                
                return response
                
        except Exception as e:
            self.logger.error(f"Failed to recall memory: {e}")
            return "I'm having trouble recalling that right now."
    
    async def _forget_memory(self, message: str) -> str:
        """Forget specific memories"""
        # Extract what to forget
        # This is simplified - would need better NLP in production
        try:
            with get_db() as db:
                # For now, just ask user to be more specific
                return "What specifically would you like me to forget? You can say things like 'forget my old address' or 'delete memories about X'."
        except Exception as e:
            self.logger.error(f"Failed to forget memory: {e}")
            return "I had trouble processing that request."
    
    def _determine_category(self, message: str) -> str:
        """Determine memory category from content"""
        message_lower = message.lower()
        
        categories = {
            'personal': ['name', 'birthday', 'age', 'i am', 'i was born'],
            'work': ['work', 'job', 'career', 'office', 'colleague', 'boss'],
            'family': ['mom', 'dad', 'mother', 'father', 'sister', 'brother', 'family'],
            'health': ['health', 'doctor', 'medicine', 'symptom', 'allergy'],
            'preferences': ['favorite', 'like', 'prefer', 'love', 'hate', 'enjoy'],
            'location': ['live', 'address', 'home', 'apartment', 'house'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in message_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def get_commands(self) -> Dict[str, str]:
        """Get available commands"""
        return {
            "tell me about...": "Recall information about a topic",
            "remember that...": "Store new information",
            "forget about...": "Remove stored information",
            "what do you know about me": "Show stored memories"
        }
