"""Plugin schemas and manifest models."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class PluginType(StrEnum):
    PROVIDER = "provider"
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    UI = "ui"


class PluginStatus(StrEnum):
    DISCOVERED = "discovered"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PluginHook(StrEnum):
    ON_LOAD = "on_load"
    ON_UNLOAD = "on_unload"
    ON_AGENT_START = "on_agent_start"
    ON_AGENT_STOP = "on_agent_stop"
    ON_TASK_CREATED = "on_task_created"
    ON_TASK_COMPLETED = "on_task_completed"
    ON_MESSAGE_RECEIVED = "on_message_received"


SUPPORTED_HOOKS = [h.value for h in PluginHook]


class PluginPermission(StrEnum):
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    AGENT_EXECUTE = "agent:execute"
    AGENT_DELEGATE = "agent:delegate"
    PROVIDER_READ = "provider:read"
    PROVIDER_WRITE = "provider:write"
    TASK_READ = "task:read"
    TASK_WRITE = "task:write"
    BUS_PUBLISH = "bus:publish"
    BUS_SUBSCRIBE = "bus:subscribe"
    SYSTEM_CONFIG = "system:config"
    NETWORK = "network"


class PluginManifest(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    plugin_type: PluginType = PluginType.TOOL
    entrypoint: str = "plugin.py"
    dependencies: list[str] = []
    permissions: list[PluginPermission] = []
    hooks: list[str] = []
    config_schema: dict = {}


class PluginCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    plugin_type: PluginType = PluginType.TOOL
    entrypoint: str = "plugin.py"
    dependencies: list[str] = []
    permissions: list[PluginPermission] = []
    hooks: list[str] = []
    source: str = ""


class PluginResponse(BaseModel):
    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    status: PluginStatus
    hooks: list[str] = []
    permissions: list[str] = []
    dependencies: list[str] = []
    error: str = ""
    loaded_at: str = ""
    directory: str = ""


class PluginEnableDisable(BaseModel):
    enabled: bool


def now_iso() -> str:
    return datetime.now(UTC).isoformat()
