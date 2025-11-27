"""
Memory Plugin - Core memory functionality (Always enabled)
"""
from core.plugin import Plugin
from core.models import Memory
from core.database import get_db
from datetime import datetime
from typing import Dict, Any, Optional


class MemoryPlugin(Plugin):
    """Core memory system - always active"""
    
    name = "Memory"
    description = "Core memory system for context and recall"
    version = "1.0.0"
    priority = 1  # Highest priority
    
    keywords = []  # No keywords - works in background
    
    async def initialize(self):
        """Initialize plugin"""
        self.logger.info(f"{self.name} initialized")
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """This plugin works in the background, doesn't handle messages directly"""
        return False
    
    async def handle(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Not used - memory works in background"""
        return None
    
    async def store_context(self, message: str, response: str, importance: float = 0.5):
        """Store important context for future reference"""
        try:
            # Determine if this should be stored as long-term memory
            if importance > 0.6:
                with get_db() as db:
                    memory = Memory(
                        user_id=self.agent.current_user_id,
                        category='conversation',
                        content=f"User: {message}\nAgent: {response}",
                        importance=importance,
                        created_at=datetime.utcnow()
                    )
                    db.add(memory)
                    db.commit()
                    
        except Exception as e:
            self.logger.error(f"Failed to store context: {e}")
    
    async def recall_relevant_memories(self, query: str, limit: int = 5) -> list:
        """Recall memories relevant to current query"""
        try:
            with get_db() as db:
                # Simple relevance - would use embeddings in production
                memories = db.query(Memory).filter(
                    Memory.user_id == self.agent.current_user_id
                ).order_by(
                    Memory.importance.desc(),
                    Memory.last_accessed.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'content': m.content,
                        'category': m.category,
                        'importance': m.importance,
                        'date': m.created_at
                    }
                    for m in memories
                ]
                
        except Exception as e:
            self.logger.error(f"Failed to recall memories: {e}")
            return []
