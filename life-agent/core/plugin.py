"""
Plugin system base classes and utilities
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """Base class for all plugins"""
    
    # Plugin metadata (override in subclass)
    name: str = "Base Plugin"
    description: str = "Base plugin description"
    version: str = "1.0.0"
    author: str = "System"
    
    # Plugin configuration
    enabled: bool = True
    priority: int = 100  # Lower = higher priority
    
    # Keywords that trigger this plugin (optional)
    keywords: List[str] = []
    
    # Required dependencies (pip packages)
    requirements: List[str] = []
    
    def __init__(self, agent_core):
        """
        Initialize plugin with reference to agent core
        
        Args:
            agent_core: Reference to main agent instance
        """
        self.agent = agent_core
        self.config = {}
        self.logger = logging.getLogger(f"plugin.{self.name}")
    
    @abstractmethod
    async def initialize(self):
        """
        Initialize plugin (called once at startup)
        Override to set up connections, load data, etc.
        """
        pass
    
    async def shutdown(self):
        """
        Clean shutdown (called when agent stops)
        Override to close connections, save data, etc.
        """
        pass
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """
        Determine if this plugin should handle the message
        
        Args:
            message: User message
            context: Conversation context
            
        Returns:
            True if plugin should handle this message
        """
        # Default: Check if any keywords are in message
        if self.keywords:
            message_lower = message.lower()
            return any(keyword.lower() in message_lower for keyword in self.keywords)
        return False
    
    @abstractmethod
    async def handle(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Handle a message and return response
        
        Args:
            message: User message
            context: Conversation context including user info
            
        Returns:
            Response string or None if plugin doesn't handle
        """
        pass
    
    def get_commands(self) -> Dict[str, str]:
        """
        Get available commands for this plugin
        
        Returns:
            Dict of command: description
        """
        return {}
    
    async def on_scheduled_task(self, task_name: str, params: Dict[str, Any]):
        """
        Handle scheduled tasks
        
        Args:
            task_name: Name of the scheduled task
            params: Task parameters
        """
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get plugin configuration value"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """Set plugin configuration value"""
        self.config[key] = value
    
    async def store_data(self, key: str, value: Any):
        """Store plugin-specific data in database"""
        from core.models import PluginData
        from core.database import get_db
        
        with get_db() as db:
            # Check if exists
            data = db.query(PluginData).filter(
                PluginData.plugin_name == self.name,
                PluginData.data_key == key,
                PluginData.user_id == self.agent.current_user_id
            ).first()
            
            if data:
                data.data_value = value
            else:
                data = PluginData(
                    user_id=self.agent.current_user_id,
                    plugin_name=self.name,
                    data_key=key,
                    data_value=value
                )
                db.add(data)
            
            db.commit()
    
    async def load_data(self, key: str) -> Optional[Any]:
        """Load plugin-specific data from database"""
        from core.models import PluginData
        from core.database import get_db
        
        with get_db() as db:
            data = db.query(PluginData).filter(
                PluginData.plugin_name == self.name,
                PluginData.data_key == key,
                PluginData.user_id == self.agent.current_user_id
            ).first()
            
            return data.data_value if data else None


class PluginMetadata:
    """Plugin metadata storage"""
    
    def __init__(self, plugin_class: type):
        self.plugin_class = plugin_class
        self.name = plugin_class.name
        self.description = plugin_class.description
        self.version = plugin_class.version
        self.enabled = plugin_class.enabled
        self.priority = plugin_class.priority
        self.requirements = plugin_class.requirements
