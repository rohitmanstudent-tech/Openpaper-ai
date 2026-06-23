"""Grok (xAI) provider plugin — wraps GrokProvider as a ProviderPlugin."""

import logging
from collections.abc import AsyncIterator

from app.core.plugin_base import ProviderPlugin

logger = logging.getLogger(__name__)


class GrokPlugin(ProviderPlugin):
    name = "grok"
    version = "1.0.0"
    description = "Grok-2 and Grok-2-mini with streaming, cost tracking, and token tracking"

    def __init__(self):
        super().__init__()
        self._provider = None

    async def _get_provider(self):
        if self._provider is None:
            from app.config import get_settings
            from app.providers.grok import GrokProvider
            settings = get_settings()
            self._provider = GrokProvider(
                api_key=settings.GROK_API_KEY or "",
                base_url=getattr(settings, "GROK_BASE_URL", "https://api.x.ai"),
            )
        return self._provider

    async def on_load(self) -> None:
        logger.info("Grok plugin loaded")

    async def on_unload(self) -> None:
        self._provider = None
        logger.info("Grok plugin unloaded")

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
            return ["grok-2", "grok-2-mini"]
