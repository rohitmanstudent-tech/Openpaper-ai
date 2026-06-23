"""Plugin System API routes."""

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import NotFoundError
from app.core.plugin_registry import get_plugin_registry
from app.core.security import get_current_user
from app.models import User
from app.models.plugin import (
    PluginCreate,
    PluginStatus,
    PluginType,
)

router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])


@router.get("")
async def list_plugins(
    plugin_type: str | None = Query(None),
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    registry = get_plugin_registry()
    pt = PluginType(plugin_type) if plugin_type else None
    ps = PluginStatus(status) if status else None
    plugins = registry.list_plugins(plugin_type=pt, status=ps)
    return {"success": True, "plugins": plugins, "total": len(plugins)}


@router.get("/discover")
async def discover_plugins(current_user: User = Depends(get_current_user)):
    registry = get_plugin_registry()
    manifests = registry.discover()
    return {"success": True, "discovered": [m.model_dump() for m in manifests], "total": len(manifests)}


@router.post("/discover-and-load")
async def discover_and_load(current_user: User = Depends(get_current_user)):
    registry = get_plugin_registry()
    results = registry.discover_and_load()
    return {"success": True, "plugins": results, "total": len(results)}


@router.get("/{plugin_id}")
async def get_plugin(plugin_id: str, current_user: User = Depends(get_current_user)):
    registry = get_plugin_registry()
    plugins = registry.list_plugins()
    for p in plugins:
        if p.id == plugin_id:
            return {"success": True, "plugin": p}
    raise NotFoundError(f"Plugin not found: {plugin_id}")


@router.post("/install")
async def install_plugin(body: PluginCreate, current_user: User = Depends(get_current_user)):
    from app.models.plugin import PluginManifest
    registry = get_plugin_registry()
    manifest = PluginManifest(
        name=body.name,
        version=body.version,
        description=body.description,
        author=body.author,
        plugin_type=body.plugin_type,
        entrypoint=body.entrypoint,
        dependencies=body.dependencies,
        permissions=body.permissions,
        hooks=body.hooks,
    )
    if body.source:
        result = registry.load_from_source(body.name, body.source, manifest)
    else:
        result = registry.load_from_manifest(manifest)
    return {"success": True, "plugin": result}


@router.post("/{plugin_id}/enable")
async def enable_plugin(plugin_id: str, current_user: User = Depends(get_current_user)):
    registry = get_plugin_registry()
    result = registry.enable(plugin_id)
    return {"success": True, "plugin": result}


@router.post("/{plugin_id}/disable")
async def disable_plugin(plugin_id: str, current_user: User = Depends(get_current_user)):
    registry = get_plugin_registry()
    result = registry.disable(plugin_id)
    return {"success": True, "plugin": result}


@router.delete("/{plugin_id}")
async def remove_plugin(plugin_id: str, current_user: User = Depends(get_current_user)):
    registry = get_plugin_registry()
    result = registry.remove(plugin_id)
    return {"success": True, "removed": result}


@router.post("/{plugin_id}/reload")
async def reload_plugin(plugin_id: str, current_user: User = Depends(get_current_user)):
    registry = get_plugin_registry()
    result = registry.hot_reload(plugin_id)
    if not result:
        raise NotFoundError(f"Plugin not found: {plugin_id}")
    return {"success": True, "plugin": result}
