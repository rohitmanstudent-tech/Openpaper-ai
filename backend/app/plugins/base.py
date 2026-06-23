from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class PluginHook(str, Enum):
    STARTUP = "on_startup"
    SHUTDOWN = "on_shutdown"
    BEFORE_REQUEST = "before_request"
    AFTER_RESPONSE = "after_response"
    ON_AGENT_MESSAGE = "on_agent_message"
    BEFORE_PROVIDER_CALL = "before_provider_call"
    AFTER_PROVIDER_CALL = "after_provider_call"
    ON_MEMORY_CREATE = "on_memory_create"
    ON_TASK_CREATE = "on_task_create"


class BasePlugin(ABC):
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    enabled: bool = True

    @property
    @abstractmethod
    def hooks(self) -> list[PluginHook]:
        ...

    async def on_startup(self, app: Any = None) -> None:
        ...

    async def on_shutdown(self, app: Any = None) -> None:
        ...

    async def before_request(self, method: str, path: str, body: dict | None = None) -> dict | None:
        ...

    async def after_response(self, method: str, path: str, status_code: int, body: Any = None) -> None:
        ...

    async def on_agent_message(self, message: dict) -> dict | None:
        ...

    async def before_provider_call(self, provider: str, model: str, messages: list[dict]) -> list[dict] | None:
        ...

    async def after_provider_call(self, provider: str, model: str, response: dict) -> None:
        ...

    async def on_memory_create(self, memory: dict) -> dict | None:
        ...

    async def on_task_create(self, task: dict) -> dict | None:
        ...
