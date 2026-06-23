from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_plugin_manager
from app.plugins.registry import PluginManager

router = APIRouter()


@router.get("/")
async def list_plugins(pm: PluginManager = Depends(get_plugin_manager)):
    return pm.list_plugins()


@router.post("/{name}/enable")
async def enable_plugin(name: str, pm: PluginManager = Depends(get_plugin_manager)):
    plugin = pm.get_plugin(name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")
    plugin.enabled = True
    return {"status": "ok", "plugin": name, "enabled": True}


@router.post("/{name}/disable")
async def disable_plugin(name: str, pm: PluginManager = Depends(get_plugin_manager)):
    plugin = pm.get_plugin(name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")
    plugin.enabled = False
    return {"status": "ok", "plugin": name, "enabled": False}


@router.post("/{name}/reload")
async def reload_plugin(name: str, pm: PluginManager = Depends(get_plugin_manager)):
    plugin = pm.get_plugin(name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")
    await plugin.on_shutdown()
    await plugin.on_startup()
    return {"status": "ok", "plugin": name}
