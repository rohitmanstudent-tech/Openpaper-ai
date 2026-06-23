from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class BaseProvider(ABC):
    name: str = ""
    default_model: str = ""

    @abstractmethod
    async def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> str: ...

    @abstractmethod
    async def chat_stream(self, messages: list[dict], model: str | None = None, **kwargs) -> AsyncIterator[str]: ...

    @abstractmethod
    async def check_health(self) -> bool: ...

    @abstractmethod
    async def list_models(self) -> list[str]: ...
