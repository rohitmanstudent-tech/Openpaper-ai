from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncGenerator, Any
from pydantic import BaseModel


class ProviderStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    UNCONFIGURED = "unconfigured"


class ProviderAuth(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    extra_headers: dict[str, str] = {}


class ModelInfo(BaseModel):
    id: str
    provider: str
    name: str
    context_length: int = 8192
    pricing_input_per_1k: float = 0.0
    pricing_output_per_1k: float = 0.0
    capabilities: list[str] = ["chat", "streaming"]

    @property
    def supports_streaming(self) -> bool:
        return "streaming" in self.capabilities

    @property
    def supports_vision(self) -> bool:
        return "vision" in self.capabilities

    @property
    def supports_tools(self) -> bool:
        return "tools" in self.capabilities


class ModelCapability(str, Enum):
    CHAT = "chat"
    STREAMING = "streaming"
    VISION = "vision"
    TOOLS = "tools"
    JSON_MODE = "json_mode"
    EMBEDDINGS = "embeddings"
    CODE = "code"
    REASONING = "reasoning"


class BaseProvider(ABC):
    provider_name: str = ""
    default_model: str = ""
    config: ProviderAuth = ProviderAuth()
    models: list[ModelInfo] = []
    status: ProviderStatus = ProviderStatus.UNCONFIGURED

    def __init__(self, config: ProviderAuth | None = None):
        if config:
            self.config = config
        self._health_check_task = None

    @abstractmethod
    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> tuple[str, dict]:
        ...

    @abstractmethod
    async def chat_stream(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[tuple[str, dict], None]:
        ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    def get_model_info(self, model_id: str) -> ModelInfo | None:
        for m in self.models:
            if m.id == model_id:
                return m
        return None

    def get_capabilities(self) -> list[str]:
        caps = set()
        for m in self.models:
            caps.update(m.capabilities)
        return sorted(caps)

    def get_pricing(self, model_id: str) -> tuple[float, float]:
        info = self.get_model_info(model_id)
        if info:
            return info.pricing_input_per_1k, info.pricing_output_per_1k
        return 0.0, 0.0
