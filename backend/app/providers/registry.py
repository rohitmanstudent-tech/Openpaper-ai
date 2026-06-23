import asyncio
import logging
from typing import AsyncGenerator

from app.config import get_settings
from app.providers.base import BaseProvider, ProviderStatus, ModelInfo

logger = logging.getLogger(__name__)
settings = get_settings()


class ProviderManager:
    def __init__(self, plugin_manager=None):
        self._providers: dict[str, BaseProvider] = {}
        self._fallback_order: list[str] = list(settings.AI_FALLBACK_ORDER)
        self._alias_map: dict[str, str] = {}
        self._model_provider_map: dict[str, str] = {}
        self._plugin_manager = plugin_manager

    # ── Registration ─────────────────────────────────────────────

    def register_provider(self, name: str, provider: BaseProvider) -> None:
        self._providers[name] = provider
        logger.info(f"Registered provider: {name}")

    def register_alias(self, alias: str, provider_name: str) -> None:
        self._alias_map[alias] = provider_name

    def register_model_map(self, model_id: str, provider_name: str) -> None:
        self._model_provider_map[model_id] = provider_name

    def get_provider(self, name: str) -> BaseProvider | None:
        resolved = self._alias_map.get(name, name)
        return self._providers.get(resolved)

    def get_all_providers(self) -> dict[str, BaseProvider]:
        return dict(self._providers)

    def set_fallback_order(self, order: list[str]) -> None:
        self._fallback_order = order

    # ── Provider detection ────────────────────────────────────────

    def detect_provider_for_model(self, model_id: str) -> str | None:
        if model_id in self._model_provider_map:
            return self._model_provider_map[model_id]
        for name, provider in self._providers.items():
            if any(m.id == model_id for m in provider.models):
                self._model_provider_map[model_id] = name
                return name
        return None

    def _resolve_providers(self, provider: str | None, model: str | None) -> list[str]:
        if provider:
            if provider in self._providers or provider in self._alias_map:
                yield provider
            else:
                logger.warning(f"Requested provider '{provider}' not registered")

        if model:
            detected = self.detect_provider_for_model(model)
            if detected and detected != provider:
                yield detected

        local_providers = settings.AI_LOCAL_PROVIDERS
        cloud_providers = settings.AI_CLOUD_PROVIDERS

        if settings.AI_LOCAL_FIRST:
            ordered = local_providers + cloud_providers
        else:
            ordered = cloud_providers + local_providers

        for p in ordered:
            if p != provider and p != self.detect_provider_for_model(model):
                yield p

    # ── Chat ──────────────────────────────────────────────────────

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        track_usage: bool = True,
        user_id: int | None = None,
        **kwargs,
    ) -> tuple[str, dict, str, str]:
        last_error: Exception | None = None
        tried_providers: list[str] = []

        providers_to_try = list(self._resolve_providers(provider, model))

        if not providers_to_try:
            providers_to_try = list(self._fallback_order)

        for prov_name in providers_to_try:
            prov = self.get_provider(prov_name)
            if prov is None:
                continue

            tried_providers.append(prov_name)

            try:
                available = await prov.is_available()
                if not available:
                    logger.info(f"Provider '{prov_name}' not available, skipping")
                    continue

                resp_model = model or prov.default_model
                if not resp_model:
                    resp_model = settings.AI_DEFAULT_MODEL

                hook_messages = messages
                if self._plugin_manager:
                    modified = await self._plugin_manager.before_provider_call(
                        provider=prov_name, model=resp_model, messages=hook_messages
                    )
                    if modified is not None:
                        hook_messages = modified

                content, usage = await prov.chat(
                    model=resp_model,
                    messages=hook_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                if self._plugin_manager:
                    await self._plugin_manager.after_provider_call(
                        provider=prov_name,
                        model=resp_model,
                        response={"content": content, "usage": usage},
                    )

                return content, usage, prov_name, resp_model

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Provider '{prov_name}' failed: {type(e).__name__}: {e}"
                )

        raise ProviderChainExhausted(
            all_providers_failed=tried_providers,
            last_error=str(last_error) if last_error else "No providers configured",
        )

    async def chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        track_usage: bool = True,
        user_id: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[dict, None]:
        last_error: Exception | None = None
        tried_providers: list[str] = []

        providers_to_try = list(self._resolve_providers(provider, model))

        if not providers_to_try:
            providers_to_try = list(self._fallback_order)

        for prov_name in providers_to_try:
            prov = self.get_provider(prov_name)
            if prov is None:
                continue

            tried_providers.append(prov_name)

            try:
                available = await prov.is_available()
                if not available:
                    logger.info(f"Provider '{prov_name}' not available, skipping")
                    continue

                resp_model = model or prov.default_model
                if not resp_model:
                    resp_model = settings.AI_DEFAULT_MODEL

                hook_messages = messages
                if self._plugin_manager:
                    modified = await self._plugin_manager.before_provider_call(
                        provider=prov_name, model=resp_model, messages=hook_messages
                    )
                    if modified is not None:
                        hook_messages = modified

                full_content = ""
                async for chunk_content, cumulative_usage in prov.chat_stream(
                    model=resp_model,
                    messages=hook_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                ):
                    full_content += chunk_content
                    yield {
                        "type": "chunk",
                        "content": chunk_content,
                        "provider": prov_name,
                        "model": resp_model,
                        "done": False,
                    }

                if self._plugin_manager:
                    await self._plugin_manager.after_provider_call(
                        provider=prov_name,
                        model=resp_model,
                        response={"content": full_content, "usage": cumulative_usage},
                    )

                yield {
                    "type": "done",
                    "content": full_content,
                    "provider": prov_name,
                    "model": resp_model,
                    "usage": cumulative_usage,
                    "done": True,
                }
                return

            except Exception as e:
                last_error = e
                logger.warning(f"Provider '{prov_name}' stream failed: {e}")

        yield {
            "type": "error",
            "content": str(last_error) if last_error else "No providers configured",
            "providers_tried": tried_providers,
            "done": True,
        }

    # ── Models listing ─────────────────────────────────────────────

    async def get_all_models(self) -> list[dict]:
        results = []
        for name, prov in self._providers.items():
            try:
                models = await prov.list_models()
                for m in models:
                    results.append({
                        "id": m.id,
                        "provider": name,
                        "name": m.name,
                        "context_length": m.context_length,
                        "pricing_input_per_1k": m.pricing_input_per_1k,
                        "pricing_output_per_1k": m.pricing_output_per_1k,
                        "capabilities": m.capabilities,
                        "available": prov.status == ProviderStatus.AVAILABLE,
                    })
            except Exception as e:
                logger.warning(f"Failed to list models for '{name}': {e}")
        return results

    async def get_providers_status(self) -> list[dict]:
        results = []
        for name, prov in self._providers.items():
            try:
                is_avail = await prov.is_available()
                prov.status = ProviderStatus.AVAILABLE if is_avail else ProviderStatus.UNAVAILABLE
            except Exception:
                prov.status = ProviderStatus.ERROR

            results.append({
                "name": name,
                "status": prov.status.value,
                "default_model": prov.default_model,
                "model_count": len(prov.models),
                "capabilities": prov.get_capabilities(),
                "local": name in settings.AI_LOCAL_PROVIDERS,
            })
        return results

    async def compare_models(
        self,
        prompt: str,
        models: list[str],
        temperature: float = 0.3,
        max_tokens: int | None = 512,
    ) -> list[dict]:
        messages = [{"role": "user", "content": prompt}]
        results = []

        async def query_single(model_id: str) -> dict:
            detected_provider = self.detect_provider_for_model(model_id)
            if not detected_provider:
                return {"model": model_id, "error": "Unknown model", "latency_ms": 0}

            start = asyncio.get_event_loop().time()
            try:
                content, usage, prov, mdl = await self.chat(
                    messages=messages,
                    model=model_id,
                    provider=detected_provider,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                latency = (asyncio.get_event_loop().time() - start) * 1000
                return {
                    "model": model_id,
                    "provider": prov,
                    "content": content,
                    "latency_ms": round(latency, 1),
                    "usage": usage,
                    "error": None,
                }
            except Exception as e:
                latency = (asyncio.get_event_loop().time() - start) * 1000
                return {
                    "model": model_id,
                    "error": str(e),
                    "latency_ms": round(latency, 1),
                }

        tasks = [query_single(m) for m in models]
        completed = await asyncio.gather(*tasks)
        return completed


class ProviderChainExhausted(Exception):
    def __init__(self, all_providers_failed: list[str], last_error: str):
        self.all_providers_failed = all_providers_failed
        self.last_error = last_error
        super().__init__(
            f"All providers failed. Tried: {all_providers_failed}. "
            f"Last error: {last_error}"
        )
