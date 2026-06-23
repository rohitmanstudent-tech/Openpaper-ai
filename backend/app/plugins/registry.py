import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any, Callable
from collections import defaultdict

from app.plugins.base import BasePlugin, PluginHook


class PluginManager:
    def __init__(self):
        self._plugins: dict[str, BasePlugin] = {}
        self._hook_map: defaultdict[PluginHook, list[BasePlugin]] = defaultdict(list)

    def register(self, plugin: BasePlugin) -> None:
        if not plugin.name:
            raise ValueError("Plugin must have a name")
        self._plugins[plugin.name] = plugin
        for hook in plugin.hooks:
            self._hook_map[hook].append(plugin)

    def unregister(self, name: str) -> None:
        plugin = self._plugins.pop(name, None)
        if plugin:
            for hook in plugin.hooks:
                if plugin in self._hook_map[hook]:
                    self._hook_map[hook].remove(plugin)

    def get_plugin(self, name: str) -> BasePlugin | None:
        return self._plugins.get(name)

    def list_plugins(self) -> list[dict]:
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "enabled": p.enabled,
                "hooks": [h.value for h in p.hooks],
            }
            for p in self._plugins.values()
        ]

    def discover(self, *paths: str) -> list[str]:
        discovered = []
        for path in paths:
            pkg_path = Path(path)
            if not pkg_path.is_dir():
                continue
            for importer, modname, ispkg in pkgutil.iter_modules([str(pkg_path)]):
                if ispkg:
                    continue
                try:
                    module = importlib.import_module(modname)
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            issubclass(obj, BasePlugin)
                            and obj is not BasePlugin
                            and not inspect.isabstract(obj)
                        ):
                            instance = obj()
                            self.register(instance)
                            discovered.append(instance.name)
                except Exception:
                    continue
        return discovered

    async def dispatch(self, hook: PluginHook | str, **kwargs: Any) -> list[Any]:
        if isinstance(hook, str):
            hook = PluginHook(hook)
        results = []
        for plugin in self._hook_map.get(hook, []):
            if not plugin.enabled:
                continue
            method: Callable | None = getattr(plugin, hook.value, None)
            if method is None:
                continue
            try:
                sig = inspect.signature(method)
                filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
                result = await method(**filtered_kwargs)
                results.append(result)
            except Exception:
                continue
        return results

    async def startup(self, app: Any = None) -> None:
        await self.dispatch(PluginHook.STARTUP, app=app)

    async def shutdown(self, app: Any = None) -> None:
        await self.dispatch(PluginHook.SHUTDOWN, app=app)

    async def before_request(self, method: str, path: str, body: dict | None = None) -> dict | None:
        results = await self.dispatch(PluginHook.BEFORE_REQUEST, method=method, path=path, body=body)
        for r in results:
            if r is not None:
                return r
        return None

    async def after_response(self, method: str, path: str, status_code: int, body: Any = None) -> None:
        await self.dispatch(PluginHook.AFTER_RESPONSE, method=method, path=path, status_code=status_code, body=body)

    async def on_agent_message(self, message: dict) -> dict | None:
        results = await self.dispatch(PluginHook.ON_AGENT_MESSAGE, message=message)
        for r in results:
            if r is not None:
                return r
        return None

    async def before_provider_call(self, provider: str, model: str, messages: list[dict]) -> list[dict] | None:
        results = await self.dispatch(PluginHook.BEFORE_PROVIDER_CALL, provider=provider, model=model, messages=messages)
        for r in results:
            if r is not None:
                return r
        return None

    async def after_provider_call(self, provider: str, model: str, response: dict) -> None:
        await self.dispatch(PluginHook.AFTER_PROVIDER_CALL, provider=provider, model=model, response=response)

    async def on_memory_create(self, memory: dict) -> dict | None:
        results = await self.dispatch(PluginHook.ON_MEMORY_CREATE, memory=memory)
        for r in results:
            if r is not None:
                return r
        return None

    async def on_task_create(self, task: dict) -> dict | None:
        results = await self.dispatch(PluginHook.ON_TASK_CREATE, task=task)
        for r in results:
            if r is not None:
                return r
        return None
