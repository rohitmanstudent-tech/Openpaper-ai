import logging
from collections.abc import AsyncIterator

import httpx

from app.providers.anthropic import AnthropicProvider
from app.providers.base import BaseProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.gemini import GeminiProvider
from app.providers.grok import GrokProvider
from app.providers.nim import NimProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider
from app.providers.openrouter import OpenRouterProvider

logger = logging.getLogger(__name__)

_registry: dict[str, BaseProvider] = {}

FALLBACK_CHAINS: dict[str, list[str]] = {
    "deepseek": ["openai", "openrouter"],
    "grok": ["openai", "openrouter"],
    "nim": ["openai"],
    "gemini": ["openrouter"],
    "openrouter": ["openai"],
    "claude": ["openrouter"],
    "ollama": [],
}


def register_providers():
    providers = [
        OllamaProvider(),
        OpenAIProvider(),
        AnthropicProvider(),
        OpenRouterProvider(),
        GeminiProvider(),
        DeepSeekProvider(),
        GrokProvider(),
        NimProvider(),
    ]
    for p in providers:
        _registry[p.name] = p


def get_provider(name: str) -> BaseProvider | None:
    return _registry.get(name)


def get_providers() -> dict[str, BaseProvider]:
    return _registry


def get_available_providers() -> dict[str, BaseProvider]:
    result = {}
    for k, v in _registry.items():
        if hasattr(v, 'api_key') and v.api_key or not hasattr(v, 'api_key'):
            result[k] = v
    return result


def get_fallback_chain(provider_name: str) -> list[str]:
    return FALLBACK_CHAINS.get(provider_name, [])


def set_fallback_chain(provider_name: str, chain: list[str]) -> None:
    FALLBACK_CHAINS[provider_name] = chain


def _is_fallthrough_error(e: Exception) -> bool:
    if isinstance(e, httpx.HTTPStatusError):
        return e.response.status_code >= 500
    if isinstance(e, httpx.TimeoutException):
        return True
    if isinstance(e, httpx.NetworkError):
        return True
    if isinstance(e, httpx.ConnectError):
        return True
    msg = str(e).lower()
    fallthrough_keywords = ["timeout", "unavailable", "connection", "refused", "resolve", "eof", "bad gateway", "service unavailable"]
    return any(kw in msg for kw in fallthrough_keywords)


async def chat_with_fallback(
    messages: list[dict],
    provider: str = "ollama",
    model: str | None = None,
    **kwargs,
) -> str:
    seen = {provider}
    chain = [provider] + get_fallback_chain(provider)
    for attempt, name in enumerate(chain):
        if name in seen and attempt > 0:
            continue
        seen.add(name)
        prov = get_provider(name)
        if not prov:
            continue
        try:
            return await prov.chat(messages, model=model, **kwargs)
        except Exception as e:
            if attempt < len(chain) - 1 and _is_fallthrough_error(e):
                logger.warning("Provider '%s' failed (%s), falling back to '%s'", name, e, chain[attempt + 1] if attempt + 1 < len(chain) else "none")
                continue
            raise
    raise RuntimeError(f"No available provider in chain: {chain}")


async def chat_stream_with_fallback(
    messages: list[dict],
    provider: str = "ollama",
    model: str | None = None,
    **kwargs,
) -> AsyncIterator[str]:
    seen = {provider}
    chain = [provider] + get_fallback_chain(provider)
    for attempt, name in enumerate(chain):
        if name in seen and attempt > 0:
            continue
        seen.add(name)
        prov = get_provider(name)
        if not prov:
            continue
        try:
            async for chunk in prov.chat_stream(messages, model=model, **kwargs):
                yield chunk
            return
        except Exception as e:
            if attempt < len(chain) - 1 and _is_fallthrough_error(e):
                logger.warning("Stream provider '%s' failed (%s), falling back to '%s'", name, e, chain[attempt + 1] if attempt + 1 < len(chain) else "none")
                continue
            raise
    raise RuntimeError(f"No available provider in chain: {chain}")
