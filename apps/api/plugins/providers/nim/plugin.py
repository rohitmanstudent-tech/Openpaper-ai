"""NVIDIA NIM provider plugin — wraps NimProvider as a ProviderPlugin."""

import logging
from collections.abc import AsyncIterator

from app.core.plugin_base import ProviderPlugin

logger = logging.getLogger(__name__)


class NimPlugin(ProviderPlugin):
    name = "nim"
    version = "1.0.0"
    description = "NVIDIA NIM — local-first, GPU-accelerated with RTX optimization and cloud fallback"

    def __init__(self):
        super().__init__()
        self._provider = None

    async def _get_provider(self):
        if self._provider is None:
            from app.config import get_settings
            from app.providers.nim import NimProvider
            settings = get_settings()
            self._provider = NimProvider(
                api_key=getattr(settings, "NVIDIA_API_KEY", ""),
                base_url=getattr(settings, "NIM_BASE_URL", "http://localhost:8000"),
            )
        return self._provider

    async def on_load(self) -> None:
        logger.info("NIM plugin loaded")

    async def on_unload(self) -> None:
        self._provider = None
        logger.info("NIM plugin unloaded")

    async def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> str:
        provider = await self._get_provider()
        return await provider.chat(messages, model=model, **kwargs)

    async def chat_stream(self, messages: list[dict], model: str | None = None, **kwargs) -> AsyncIterator[str]:
        provider = await self._get_provider()
        async for chunk in provider.chat_stream(messages, model=model, **kwargs):
            yield chunk

    async def check_health(self) -> bool:
        try:
            provider = await self._get_provider()
            return await provider.check_health()
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            provider = await self._get_provider()
            return await provider.list_models()
        except Exception:
            return ["meta/llama-3.1-8b-instruct"]
