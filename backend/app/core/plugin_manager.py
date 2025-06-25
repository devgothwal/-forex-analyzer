"""
Plugin Manager - Core extensibility system for the Forex Analyzer
Implements plugin discovery, loading, and lifecycle management
"""

import importlib
import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    DISCOVERED = "discovered"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str
    author: str
    api_version: str
    dependencies: List[str] = None
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.permissions is None:
            self.permissions = []


class PluginInterface(ABC):
    """Base interface for all plugins"""
    
    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest
        self._config = {}
        self._status = PluginStatus.DISCOVERED
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources when plugin is unloaded"""
        pass
    
    @property
    def status(self) -> PluginStatus:
        return self._status
    
    def set_status(self, status: PluginStatus):
        self._status = status


class AnalysisPlugin(PluginInterface):
    """Interface for trading analysis plugins"""
    
    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis on trading data"""
        pass
    
    @abstractmethod
    async def get_insights(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from analysis results"""
        pass
    
    async def visualize(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Optional: Generate visualization data"""
        return {}


class DataSourcePlugin(PluginInterface):
    """Interface for data source plugins"""
    
    @abstractmethod
    async def validate(self, file_data: bytes) -> bool:
        """Validate if file can be processed by this plugin"""
        pass
    
    @abstractmethod
    async def parse(self, file_data: bytes) -> Dict[str, Any]:
        """Parse file data into standardized format"""
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """Get the expected data schema"""
        pass


class EventBus:
    """Event system for plugin communication"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[callable]] = {}
        self._logger = logging.getLogger(f"{__name__}.EventBus")
    
    def subscribe(self, event_type: str, handler: callable):
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        self._logger.debug(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: callable):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                self._logger.debug(f"Unsubscribed from event: {event_type}")
            except ValueError:
                pass
    
    async def emit(self, event_type: str, payload: Any, source: str = "system"):
        """Emit an event to all subscribers"""
        if event_type not in self._subscribers:
            return
        
        event = {
            "type": event_type,
            "payload": payload,
            "source": source,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        self._logger.debug(f"Emitting event: {event_type} from {source}")
        
        # Execute all handlers concurrently
        handlers = self._subscribers[event_type][:]
        if handlers:
            await asyncio.gather(
                *[self._safe_execute_handler(handler, event) for handler in handlers],
                return_exceptions=True
            )
    
    async def _safe_execute_handler(self, handler: callable, event: Dict[str, Any]):
        """Safely execute event handler with error handling"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            self._logger.error(f"Error in event handler: {e}")


class PluginManager:
    """Central plugin management system"""
    
    def __init__(self, plugin_dirs: List[str] = None):
        self.plugin_dirs = plugin_dirs or ["plugins", "../plugins"]
        self.plugins: Dict[str, PluginInterface] = {}
        self.event_bus = EventBus()
        self._logger = logging.getLogger(f"{__name__}.PluginManager")
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
    
    async def discover_plugins(self) -> List[str]:
        """Discover all available plugins"""
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            plugin_path = Path(plugin_dir)
            if not plugin_path.exists():
                continue
            
            # Look for plugin directories
            for item in plugin_path.iterdir():
                if item.is_dir() and (item / "manifest.json").exists():
                    try:
                        manifest = self._load_manifest(item / "manifest.json")
                        discovered.append(manifest.name)
                        self._logger.info(f"Discovered plugin: {manifest.name}")
                    except Exception as e:
                        self._logger.error(f"Error loading manifest from {item}: {e}")
        
        await self.event_bus.emit("plugins_discovered", {"plugins": discovered})
        return discovered
    
    async def load_plugin(self, plugin_name: str) -> bool:
        """Load a specific plugin"""
        try:
            plugin_path = self._find_plugin_path(plugin_name)
            if not plugin_path:
                self._logger.error(f"Plugin not found: {plugin_name}")
                return False
            
            # Load manifest
            manifest_path = plugin_path / "manifest.json"
            manifest = self._load_manifest(manifest_path)
            
            # Add plugin directory to Python path
            sys.path.insert(0, str(plugin_path))
            
            try:
                # Import plugin module
                module = importlib.import_module("plugin")
                
                # Get plugin class
                plugin_class = getattr(module, "Plugin", None)
                if not plugin_class:
                    raise ImportError("Plugin class not found")
                
                # Create plugin instance
                plugin = plugin_class(manifest)
                plugin.set_status(PluginStatus.LOADING)
                
                # Initialize plugin
                config = self._plugin_configs.get(plugin_name, {})
                await plugin.initialize(config)
                
                # Register plugin
                self.plugins[plugin_name] = plugin
                plugin.set_status(PluginStatus.ACTIVE)
                
                self._logger.info(f"Loaded plugin: {plugin_name}")
                await self.event_bus.emit("plugin_loaded", {
                    "plugin": plugin_name,
                    "manifest": manifest.__dict__
                })
                
                return True
                
            finally:
                # Remove plugin directory from Python path
                sys.path.remove(str(plugin_path))
        
        except Exception as e:
            self._logger.error(f"Error loading plugin {plugin_name}: {e}")
            if plugin_name in self.plugins:
                self.plugins[plugin_name].set_status(PluginStatus.ERROR)
            await self.event_bus.emit("plugin_error", {
                "plugin": plugin_name,
                "error": str(e)
            })
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin"""
        if plugin_name not in self.plugins:
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            await plugin.cleanup()
            del self.plugins[plugin_name]
            
            self._logger.info(f"Unloaded plugin: {plugin_name}")
            await self.event_bus.emit("plugin_unloaded", {"plugin": plugin_name})
            return True
        
        except Exception as e:
            self._logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    async def load_all_plugins(self) -> Dict[str, bool]:
        """Load all discovered plugins"""
        discovered = await self.discover_plugins()
        results = {}
        
        for plugin_name in discovered:
            results[plugin_name] = await self.load_plugin(plugin_name)
        
        return results
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get a loaded plugin by name"""
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: Type[PluginInterface]) -> List[PluginInterface]:
        """Get all plugins of a specific type"""
        return [plugin for plugin in self.plugins.values() 
                if isinstance(plugin, plugin_type)]
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all plugins with their status"""
        return {
            name: {
                "manifest": plugin.manifest.__dict__,
                "status": plugin.status.value
            }
            for name, plugin in self.plugins.items()
        }
    
    def configure_plugin(self, plugin_name: str, config: Dict[str, Any]):
        """Set configuration for a plugin"""
        self._plugin_configs[plugin_name] = config
    
    def _find_plugin_path(self, plugin_name: str) -> Optional[Path]:
        """Find the path to a plugin directory"""
        for plugin_dir in self.plugin_dirs:
            plugin_path = Path(plugin_dir) / plugin_name
            if plugin_path.exists() and (plugin_path / "manifest.json").exists():
                return plugin_path
        return None
    
    def _load_manifest(self, manifest_path: Path) -> PluginManifest:
        """Load plugin manifest from JSON file"""
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        return PluginManifest(**data)


# Global plugin manager instance
plugin_manager = PluginManager()