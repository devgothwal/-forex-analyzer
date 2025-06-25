"""
Plugin Management Endpoints - Plugin lifecycle and management
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException

from app.core.plugin_manager import plugin_manager
from app.core.event_system import event_manager

router = APIRouter()


@router.get("/")
async def list_plugins():
    """List all available plugins with their status"""
    return plugin_manager.list_plugins()


@router.post("/{plugin_name}/load")
async def load_plugin(plugin_name: str):
    """Load a specific plugin"""
    success = await plugin_manager.load_plugin(plugin_name)
    
    if success:
        return {"message": f"Plugin {plugin_name} loaded successfully"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to load plugin {plugin_name}")


@router.post("/{plugin_name}/unload")
async def unload_plugin(plugin_name: str):
    """Unload a specific plugin"""
    success = await plugin_manager.unload_plugin(plugin_name)
    
    if success:
        return {"message": f"Plugin {plugin_name} unloaded successfully"}
    else:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")


@router.get("/{plugin_name}/status")
async def get_plugin_status(plugin_name: str):
    """Get detailed status of a specific plugin"""
    plugin = plugin_manager.get_plugin(plugin_name)
    
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return {
        "name": plugin.manifest.name,
        "version": plugin.manifest.version,
        "status": plugin.status.value,
        "manifest": plugin.manifest.__dict__
    }


@router.post("/discover")
async def discover_plugins():
    """Discover available plugins"""
    discovered = await plugin_manager.discover_plugins()
    return {"discovered_plugins": discovered}


@router.post("/reload-all")
async def reload_all_plugins():
    """Reload all currently loaded plugins"""
    current_plugins = list(plugin_manager.plugins.keys())
    results = {}
    
    for plugin_name in current_plugins:
        # Unload
        unload_success = await plugin_manager.unload_plugin(plugin_name)
        # Reload
        load_success = await plugin_manager.load_plugin(plugin_name) if unload_success else False
        results[plugin_name] = load_success
    
    return {"reload_results": results}