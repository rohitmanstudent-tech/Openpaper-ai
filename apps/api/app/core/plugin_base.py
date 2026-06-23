"""Abstract base classes for all plugin types.

Each plugin type extends BasePlugin with type-specific interfaces.
"""

import abc
import logging
from typing import Any

from app.models.plugin import PluginHook, PluginManifest, PluginType

logger = logging.getLogger(__name__)


class BasePlugin(abc.ABC):
    """Abstract base for all plugins.

    Subclasses must set:
        name, version, description, plugin_type
    """

    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    plugin_type: PluginType = PluginType.TOOL
    manifest: PluginManifest | None = None
    _enabled: bool = False
    _loaded: bool = False

    # ── Lifecycle Hooks ────────────────────────────────────────────────

    async def on_load(self) -> None:
        """Called when plugin is loaded into the registry."""
        logger.info("Plugin loaded: %s v%s", self.name, self.version)

    async def on_unload(self) -> None:
        """Called when plugin is unloaded from the registry."""
        logger.info("Plugin unloaded: %s", self.name)

    async def on_agent_start(self, agent_id: str, config: dict | None = None) -> None:
        """Called when an agent starts."""

    async def on_agent_stop(self, agent_id: str) -> None:
        """Called when an agent stops."""

    async def on_task_created(self, task_data: dict) -> None:
        """Called when a task is created."""

    async def on_task_completed(self, task_data: dict) -> None:
        """Called when a task completes."""

    async def on_message_received(self, message: dict) -> None:
        """Called when a message is received on the bus."""

    # ── Internal ───────────────────────────────────────────────────────

    def get_hooks(self) -> list[str]:
        return [h.value for h in PluginHook]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "plugin_type": self.plugin_type.value,
            "enabled": self._enabled,
        }


class ProviderPlugin(BasePlugin):
    """Plugin that adds a new LLM provider."""

    plugin_type = PluginType.PROVIDER

    @abc.abstractmethod
    async def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> str:
        ...

    @abc.abstractmethod
    async def chat_stream(self, messages: list[dict], model: str | None = None, **kwargs) -> Any:
        ...

    @abc.abstractmethod
    async def check_health(self) -> bool:
        ...

    async def list_models(self) -> list[str]:
        return []


class AgentPlugin(BasePlugin):
    """Plugin that adds a new agent type."""

    plugin_type = PluginType.AGENT

    @abc.abstractmethod
    async def process(self, user_input: str, context: list[dict] | None = None) -> str:
        ...

    @abc.abstractmethod
    async def process_stream(self, user_input: str, context: list[dict] | None = None) -> Any:
        ...


class ToolPlugin(BasePlugin):
    """Plugin that adds a tool/function."""

    plugin_type = PluginType.TOOL

    @abc.abstractmethod
    async def execute(self, params: dict) -> Any:
        ...

    def get_tool_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {},
        }


class WorkflowPlugin(BasePlugin):
    """Plugin that defines a multi-step workflow."""

    plugin_type = PluginType.WORKFLOW

    @abc.abstractmethod
    async def run(self, inputs: dict) -> Any:
        ...

    def get_steps(self) -> list[dict]:
        return []


class UIPlugin(BasePlugin):
    """Plugin that provides frontend components."""

    plugin_type = PluginType.UI

    @abc.abstractmethod
    def get_components(self) -> list[dict]:
        ...

    def get_routes(self) -> list[dict]:
        return []
