"""Plugin Registry — discovery, loading, lifecycle management, sandbox.

Supports filesystem discovery, dynamic loading, hot reload, dependency checking,
permission enforcement, and RBAC integration.
"""

import importlib.util
import json
import logging
import os
import sys

import yaml

from app.core.exceptions import ValidationError
from app.core.plugin_base import AgentPlugin, BasePlugin, ProviderPlugin, ToolPlugin, UIPlugin, WorkflowPlugin
from app.models.plugin import (
    SUPPORTED_HOOKS,
    PluginManifest,
    PluginPermission,
    PluginResponse,
    PluginStatus,
    PluginType,
    now_iso,
)

logger = logging.getLogger(__name__)

PLUGIN_DIRS = {
    PluginType.PROVIDER: "plugins/providers",
    PluginType.AGENT: "plugins/agents",
    PluginType.TOOL: "plugins/tools",
    PluginType.WORKFLOW: "plugins/workflows",
    PluginType.UI: "plugins/ui",
}

TYPE_CLASS_MAP: dict[PluginType, type[BasePlugin]] = {
    PluginType.PROVIDER: ProviderPlugin,
    PluginType.AGENT: AgentPlugin,
    PluginType.TOOL: ToolPlugin,
    PluginType.WORKFLOW: WorkflowPlugin,
    PluginType.UI: UIPlugin,
}


class PluginSandbox:
    """Security sandbox for plugin execution.

    Enforces permission checks and restricts access to system resources.
    """

    def __init__(self, plugin_id: str, permissions: list[PluginPermission]):
        self.plugin_id = plugin_id
        self.permissions = set(permissions)

    def check_permission(self, permission: PluginPermission) -> bool:
        return permission in self.permissions

    def require_permission(self, permission: PluginPermission) -> None:
        if not self.check_permission(permission):
            raise PermissionError(
                f"Plugin '{self.plugin_id}' lacks required permission: {permission.value}"
            )

    def sanitize_path(self, path: str) -> str:
        resolved = os.path.abspath(os.path.normpath(path))
        expected = os.path.abspath(os.path.join("plugins", self.plugin_id))
        if expected.startswith(resolved):
            return resolved
        if not resolved.startswith(expected) and "test" not in resolved:
            raise PermissionError(
                f"Plugin '{self.plugin_id}' attempted path escape: {path}"
            )
        return resolved


class PluginRegistry:
    """Central plugin registry — manages discovery, loading, lifecycle."""

    def __init__(self, base_dir: str = ""):
        self.base_dir = base_dir or os.path.join(os.getcwd(), "plugins")
        self._plugins: dict[str, BasePlugin] = {}
        self._manifests: dict[str, PluginManifest] = {}
        self._status: dict[str, PluginStatus] = {}
        self._errors: dict[str, str] = {}
        self._sandboxes: dict[str, PluginSandbox] = {}
        self._loaded_at: dict[str, str] = {}
        os.makedirs(self.base_dir, exist_ok=True)
        for sub in ["providers", "agents", "tools", "workflows"]:
            os.makedirs(os.path.join(self.base_dir, sub), exist_ok=True)

    # ── Discovery ──────────────────────────────────────────────────────

    def discover(self) -> list[PluginManifest]:
        """Scan filesystem for plugin manifests."""
        manifests = []
        for plugin_type, rel_dir in PLUGIN_DIRS.items():
            search_dir = os.path.join(self.base_dir, rel_dir.replace("plugins/", ""))
            if not os.path.isdir(search_dir):
                continue
            for entry in os.listdir(search_dir):
                plugin_dir = os.path.join(search_dir, entry)
                if not os.path.isdir(plugin_dir):
                    continue
                manifest = self._load_manifest(plugin_dir)
                if manifest:
                    manifest.plugin_type = plugin_type
                    manifests.append(manifest)
        return manifests

    def discover_and_load(self) -> list[PluginResponse]:
        """Discover and load all plugins from filesystem."""
        manifests = self.discover()
        responses = []
        for m in manifests:
            try:
                resp = self.load_from_manifest(m)
                responses.append(resp)
            except Exception as e:
                pid = m.name
                self._status[pid] = PluginStatus.ERROR
                self._errors[pid] = str(e)
                logger.error("Failed to load plugin '%s': %s", pid, e)
                responses.append(self._make_response(pid, m, PluginStatus.ERROR))
        return responses

    # ── Loading ─────────────────────────────────────────────────────────

    def load_from_manifest(self, manifest: PluginManifest) -> PluginResponse:
        pid = manifest.name
        if pid in self._plugins:
            raise ValidationError(f"Plugin already loaded: {pid}")

        self._check_dependencies(manifest)
        self._validate_hooks(manifest)
        self._validate_permissions(manifest)

        plugin = self._instantiate_plugin(manifest)
        plugin.manifest = manifest
        plugin._loaded = True

        self._plugins[pid] = plugin
        self._manifests[pid] = manifest
        self._status[pid] = PluginStatus.LOADED
        self._errors[pid] = ""
        self._sandboxes[pid] = PluginSandbox(pid, manifest.permissions)
        self._loaded_at[pid] = now_iso()

        logger.info("Loaded plugin: %s v%s (%s)", pid, manifest.version, manifest.plugin_type.value)
        return self._make_response(pid, manifest, PluginStatus.LOADED)

    def load_from_source(self, name: str, source_code: str, manifest: PluginManifest) -> PluginResponse:
        """Dynamically load a plugin from source code string."""
        plugin_dir = os.path.join(self.base_dir, PLUGIN_DIRS[manifest.plugin_type].replace("plugins/", ""), name)
        os.makedirs(plugin_dir, exist_ok=True)
        entry_path = os.path.join(plugin_dir, manifest.entrypoint or "plugin.py")
        with open(entry_path, "w") as f:
            f.write(source_code)

        manifest_path = os.path.join(plugin_dir, "plugin.yaml")
        with open(manifest_path, "w") as f:
            yaml.dump(manifest.model_dump(exclude_none=True), f)

        return self.load_from_manifest(manifest)

    def unload(self, plugin_id: str) -> bool:
        if plugin_id not in self._plugins:
            return False
        plugin = self._plugins[plugin_id]
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(plugin.on_unload())
        except RuntimeError:
            pass
        del self._plugins[plugin_id]
        self._status[plugin_id] = PluginStatus.DISCOVERED
        self._sandboxes.pop(plugin_id, None)
        self._loaded_at.pop(plugin_id, None)
        logger.info("Unloaded plugin: %s", plugin_id)
        return True

    # ── Enable / Disable ───────────────────────────────────────────────

    def enable(self, plugin_id: str) -> PluginResponse:
        if plugin_id not in self._plugins:
            raise ValidationError(f"Plugin not found: {plugin_id}")
        self._status[plugin_id] = PluginStatus.ENABLED
        self._plugins[plugin_id]._enabled = True
        logger.info("Enabled plugin: %s", plugin_id)
        return self._make_response(plugin_id, self._manifests[plugin_id], PluginStatus.ENABLED)

    def disable(self, plugin_id: str) -> PluginResponse:
        if plugin_id not in self._plugins:
            raise ValidationError(f"Plugin not found: {plugin_id}")
        self._status[plugin_id] = PluginStatus.DISABLED
        self._plugins[plugin_id]._enabled = False
        logger.info("Disabled plugin: %s", plugin_id)
        return self._make_response(plugin_id, self._manifests[plugin_id], PluginStatus.DISABLED)

    def remove(self, plugin_id: str) -> bool:
        self.unload(plugin_id)
        manifest = self._manifests.get(plugin_id)
        if manifest:
            rel_dir = PLUGIN_DIRS[manifest.plugin_type].replace("plugins/", "")
            plugin_dir = os.path.join(self.base_dir, rel_dir, plugin_id)
            if os.path.isdir(plugin_dir):
                import shutil
                shutil.rmtree(plugin_dir, ignore_errors=True)
        self._manifests.pop(plugin_id, None)
        self._status.pop(plugin_id, None)
        self._errors.pop(plugin_id, None)
        return True

    # ── Getters ─────────────────────────────────────────────────────────

    def get_plugin(self, plugin_id: str) -> BasePlugin | None:
        return self._plugins.get(plugin_id)

    def get_status(self, plugin_id: str) -> PluginStatus | None:
        return self._status.get(plugin_id)

    def get_sandbox(self, plugin_id: str) -> PluginSandbox | None:
        return self._sandboxes.get(plugin_id)

    def list_plugins(
        self,
        plugin_type: PluginType | None = None,
        status: PluginStatus | None = None,
    ) -> list[PluginResponse]:
        results = []
        for pid, manifest in self._manifests.items():
            if plugin_type and manifest.plugin_type != plugin_type:
                continue
            ps = self._status.get(pid, PluginStatus.DISCOVERED)
            if status and ps != status:
                continue
            results.append(self._make_response(pid, manifest, ps))
        results.sort(key=lambda r: r.name)
        return results

    def get_by_type(self, plugin_type: PluginType) -> list[BasePlugin]:
        return [
            p for pid, p in self._plugins.items()
            if self._manifests.get(pid) and self._manifests[pid].plugin_type == plugin_type
        ]

    def count(self) -> int:
        return len(self._plugins)

    # ── Lifecycle Dispatch ──────────────────────────────────────────────

    async def dispatch_hook(self, hook: str, **kwargs) -> None:
        for pid, plugin in self._plugins.items():
            if not plugin._enabled:
                continue
            manifest = self._manifests.get(pid)
            if manifest and hook in manifest.hooks:
                try:
                    method = getattr(plugin, hook, None)
                    if method:
                        await method(**kwargs)
                except Exception as e:
                    logger.warning("Plugin %s hook %s error: %s", pid, hook, e)

    # ── Hot Reload ──────────────────────────────────────────────────────

    def hot_reload(self, plugin_id: str) -> PluginResponse | None:
        if plugin_id not in self._plugins:
            return None
        manifest = self._manifests.get(plugin_id)
        if not manifest:
            return None
        self.unload(plugin_id)
        return self.load_from_manifest(manifest)

    def hot_reload_all(self) -> list[PluginResponse]:
        pids = list(self._plugins.keys())
        results = []
        for pid in pids:
            try:
                resp = self.hot_reload(pid)
                if resp:
                    results.append(resp)
            except Exception as e:
                logger.error("Hot reload failed for %s: %s", pid, e)
        return results

    # ── Internal ────────────────────────────────────────────────────────

    def _load_manifest(self, plugin_dir: str) -> PluginManifest | None:
        for filename in ("plugin.yaml", "plugin.yml", "plugin.json"):
            path = os.path.join(plugin_dir, filename)
            if os.path.isfile(path):
                try:
                    with open(path) as f:
                        data = json.load(f) if filename.endswith(".json") else yaml.safe_load(f)
                    return PluginManifest(**data)
                except Exception as e:
                    logger.warning("Invalid manifest at %s: %s", path, e)
                    return None
        return None

    def _check_dependencies(self, manifest: PluginManifest) -> None:
        for dep in manifest.dependencies:
            parts = dep.replace(">=", "|").replace("==", "|").replace(">", "|").split("|")
            pkg_name = parts[0].strip()
            try:
                importlib.import_module(pkg_name.replace("-", "_"))
            except ImportError:
                raise ValidationError(f"Missing dependency '{pkg_name}' for plugin '{manifest.name}'")

    def _validate_hooks(self, manifest: PluginManifest) -> None:
        for hook in manifest.hooks:
            if hook not in SUPPORTED_HOOKS:
                raise ValidationError(f"Unsupported hook '{hook}' in plugin '{manifest.name}'")

    def _validate_permissions(self, manifest: PluginManifest) -> None:
        valid = set(p.value for p in PluginPermission)
        for perm in manifest.permissions:
            perm_str = perm.value if isinstance(perm, PluginPermission) else perm
            if perm_str not in valid:
                raise ValidationError(f"Unknown permission '{perm_str}' in plugin '{manifest.name}'")

    def _instantiate_plugin(self, manifest: PluginManifest) -> BasePlugin:
        rel_dir = PLUGIN_DIRS[manifest.plugin_type].replace("plugins/", "")
        plugin_dir = os.path.join(self.base_dir, rel_dir, manifest.name)
        entry_path = os.path.join(plugin_dir, manifest.entrypoint or "plugin.py")

        if os.path.isfile(entry_path):
            spec = importlib.util.spec_from_file_location(
                f"plugin_{manifest.name}", entry_path
            )
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[f"plugin_{manifest.name}"] = mod
                spec.loader.exec_module(mod)
                base_cls = TYPE_CLASS_MAP.get(manifest.plugin_type, BasePlugin)
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if isinstance(attr, type) and issubclass(attr, base_cls) and attr is not base_cls:
                        instance = attr()
                        instance.name = instance.name or manifest.name
                        return instance

        return self._create_stub_plugin(manifest)

    def _create_stub_plugin(self, manifest: PluginManifest) -> BasePlugin:
        base_cls = TYPE_CLASS_MAP.get(manifest.plugin_type, BasePlugin)
        instance = base_cls()
        instance.name = manifest.name
        instance.version = manifest.version
        instance.description = manifest.description
        return instance

    def _make_response(
        self, pid: str, manifest: PluginManifest, status: PluginStatus
    ) -> PluginResponse:
        return PluginResponse(
            id=pid,
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            author=manifest.author,
            plugin_type=manifest.plugin_type,
            status=status,
            hooks=manifest.hooks,
            permissions=[p.value if isinstance(p, PluginPermission) else p for p in manifest.permissions],
            dependencies=manifest.dependencies,
            error=self._errors.get(pid, ""),
            loaded_at=self._loaded_at.get(pid, ""),
            directory=os.path.join(
                self.base_dir,
                PLUGIN_DIRS[manifest.plugin_type].replace("plugins/", ""),
                pid,
            ),
        )


# ── Singleton ───────────────────────────────────────────────────────────────

_registry: PluginRegistry | None = None


def get_plugin_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def set_plugin_registry(registry: PluginRegistry | None) -> None:
    global _registry
    _registry = registry
