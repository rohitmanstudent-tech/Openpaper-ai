"""ProviderManager — centralized governance for all AI providers.

Coordinates provider lifecycle, fallback routing, usage aggregation,
health monitoring, and model discovery across the provider registry.
"""

import logging
from collections.abc import AsyncIterator

from app.providers import (
    FALLBACK_CHAINS,
    chat_stream_with_fallback,
    chat_with_fallback,
    get_available_providers,
    get_fallback_chain,
    get_provider,
    get_providers,
    set_fallback_chain,
)
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    """Central governance for AI provider lifecycle and routing."""

    def __init__(self):
        self._fallback_cache: dict[str, list[str]] = dict(FALLBACK_CHAINS)

    def get_provider(self, name: str) -> BaseProvider | None:
        return get_provider(name)

    def list_providers(self) -> dict[str, BaseProvider]:
        return get_providers()

    def list_available(self) -> dict[str, BaseProvider]:
        return get_available_providers()

    def count_providers(self) -> int:
        return len(get_providers())

    def count_available(self) -> int:
        return len(get_available_providers())

    def get_fallback_chain(self, provider: str) -> list[str]:
        return get_fallback_chain(provider)

    def set_fallback_chain(self, provider: str, chain: list[str]) -> None:
        set_fallback_chain(provider, chain)
        self._fallback_cache[provider] = chain

    async def chat(
        self,
        messages: list[dict],
        provider: str = "ollama",
        model: str | None = None,
        fallback: bool = True,
        **kwargs,
    ) -> str:
        if fallback:
            return await chat_with_fallback(messages, provider=provider, model=model, **kwargs)
        prov = get_provider(provider)
        if not prov:
            raise RuntimeError(f"Provider '{provider}' not available")
        return await prov.chat(messages, model=model, **kwargs)

    async def chat_stream(
        self,
        messages: list[dict],
        provider: str = "ollama",
        model: str | None = None,
        fallback: bool = True,
        **kwargs,
    ) -> AsyncIterator[str]:
        if fallback:
            async for chunk in chat_stream_with_fallback(messages, provider=provider, model=model, **kwargs):
                yield chunk
            return
        prov = get_provider(provider)
        if not prov:
            raise RuntimeError(f"Provider '{provider}' not available")
        async for chunk in prov.chat_stream(messages, model=model, **kwargs):
            yield chunk

    async def check_provider_health(self, name: str) -> bool:
        prov = get_provider(name)
        if not prov:
            return False
        try:
            return await prov.check_health()
        except Exception:
            return False

    async def get_all_health(self) -> dict[str, bool]:
        results = {}
        for name in get_providers():
            results[name] = await self.check_provider_health(name)
        return results

    async def list_models_for(self, provider: str) -> list[str]:
        prov = get_provider(provider)
        if not prov:
            return []
        try:
            return await prov.list_models()
        except Exception:
            return []

    async def list_all_models(self) -> dict[str, list[str]]:
        results = {}
        for name in get_providers():
            models = await self.list_models_for(name)
            if models:
                results[name] = models
        return results

    def get_usage_stats(self) -> dict[str, dict]:
        stats = {}
        for name, prov in get_providers().items():
            if hasattr(prov, "get_total_usage"):
                stats[name] = prov.get_total_usage()
            elif hasattr(prov, "_usage"):
                stats[name] = {"total_calls": len(prov._usage)}
            else:
                stats[name] = {}
        return stats

    def get_provider_config(self, name: str) -> dict:
        prov = get_provider(name)
        if not prov:
            return {}
        config = {
            "name": prov.name,
            "default_model": getattr(prov, "default_model", ""),
            "has_api_key": bool(getattr(prov, "api_key", "")),
            "fallback_chain": self.get_fallback_chain(name),
        }
        if hasattr(prov, "get_total_usage"):
            config["usage"] = prov.get_total_usage()
        return config
