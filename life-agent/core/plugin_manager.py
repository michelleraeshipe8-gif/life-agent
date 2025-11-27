"""
Plugin Manager - Loads and manages all plugins
"""
import os
import importlib
import importlib.util
import yaml
from typing import Dict, List, Optional, Any
import logging
from core.plugin import Plugin, PluginMetadata

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin lifecycle and routing"""
    
    def __init__(self, agent_core, config_path: str = "config/plugins.yaml"):
        self.agent = agent_core
        self.config_path = config_path
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.config = {}
        
    def load_config(self):
        """Load plugin configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"Plugin config not found: {self.config_path}")
            self.config = {'enabled_plugins': [], 'plugin_settings': {}}
    
    async def load_plugins(self):
        """Load all enabled plugins"""
        self.load_config()
        
        enabled_plugins = self.config.get('enabled_plugins', [])
        plugin_settings = self.config.get('plugin_settings', {})
        
        logger.info(f"Loading {len(enabled_plugins)} plugins...")
        
        # Load plugins from plugins directory
        plugins_dir = 'plugins'
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
            logger.warning(f"Created plugins directory: {plugins_dir}")
            return
        
        # Scan for plugin files
        for filename in os.listdir(plugins_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                plugin_name = filename[:-3]  # Remove .py
                
                # Check if plugin is enabled
                if plugin_name not in enabled_plugins:
                    logger.debug(f"Plugin {plugin_name} is disabled, skipping")
                    continue
                
                try:
                    # Import plugin module
                    spec = importlib.util.spec_from_file_location(
                        plugin_name, 
                        os.path.join(plugins_dir, filename)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find plugin class (should inherit from Plugin)
                    plugin_class = None
                    for item_name in dir(module):
                        item = getattr(module, item_name)
                        if (isinstance(item, type) and 
                            issubclass(item, Plugin) and 
                            item != Plugin):
                            plugin_class = item
                            break
                    
                    if plugin_class:
                        # Create plugin instance
                        plugin_instance = plugin_class(self.agent)
                        
                        # Load plugin settings
                        if plugin_name in plugin_settings:
                            plugin_instance.config = plugin_settings[plugin_name]
                        
                        # Initialize plugin
                        await plugin_instance.initialize()
                        
                        # Store plugin
                        self.plugins[plugin_name] = plugin_instance
                        self.plugin_metadata[plugin_name] = PluginMetadata(plugin_class)
                        
                        logger.info(f"[OK] Loaded plugin: {plugin_instance.name} v{plugin_instance.version}")
                    else:
                        logger.warning(f"No plugin class found in {filename}")
                        
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_name}: {e}", exc_info=True)
        
        # Sort plugins by priority
        self.plugins = dict(sorted(
            self.plugins.items(), 
            key=lambda x: x[1].priority
        ))
        
        logger.info(f"Loaded {len(self.plugins)} plugins successfully")
    
    async def route_message(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Route message to appropriate plugin(s)
        
        Args:
            message: User message
            context: Conversation context
            
        Returns:
            Response from plugin or None
        """
        # Check each plugin in priority order
        for plugin_name, plugin in self.plugins.items():
            if plugin.can_handle(message, context):
                try:
                    logger.debug(f"Routing to plugin: {plugin_name}")
                    response = await plugin.handle(message, context)
                    if response:
                        return response
                except Exception as e:
                    logger.error(f"Plugin {plugin_name} error: {e}", exc_info=True)
        
        return None
    
    async def shutdown_all(self):
        """Shutdown all plugins gracefully"""
        logger.info("Shutting down plugins...")
        for plugin_name, plugin in self.plugins.items():
            try:
                await plugin.shutdown()
                logger.info(f"[OK] Shutdown: {plugin_name}")
            except Exception as e:
                logger.error(f"Error shutting down {plugin_name}: {e}")
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get plugin by name"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins with metadata"""
        return [
            {
                'name': metadata.name,
                'description': metadata.description,
                'version': metadata.version,
                'enabled': metadata.enabled,
                'priority': metadata.priority
            }
            for metadata in self.plugin_metadata.values()
        ]
    
    def get_all_commands(self) -> Dict[str, Dict[str, str]]:
        """Get all commands from all plugins"""
        all_commands = {}
        for plugin_name, plugin in self.plugins.items():
            commands = plugin.get_commands()
            if commands:
                all_commands[plugin_name] = commands
        return all_commands
