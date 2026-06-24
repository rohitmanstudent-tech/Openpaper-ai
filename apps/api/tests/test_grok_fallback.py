"""Tests for Grok plugin, usage tracking, fallback, and ProviderManager."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import yaml

from app.core.plugin_registry import PluginRegistry, set_plugin_registry
from app.providers import FALLBACK_CHAINS, get_provider, register_providers
from app.providers.grok import GrokProvider
from app.providers.manager import ProviderManager

# ── Usage Tracking ─────────────────────────────────────────────────────


class TestUsageTracking:
    def test_usage_starts_empty(self):
        p = GrokProvider()
        assert p.get_usage() == []
        assert p.get_total_usage()["total_tokens"] == 0
        assert p.get_total_usage()["cost"] == 0

    def test_usage_accumulates(self):
        p = GrokProvider()
        p._record_usage("grok-2", {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
        assert len(p.get_usage()) == 1
        total = p.get_total_usage()
        assert total["prompt_tokens"] == 10
        assert total["completion_tokens"] == 5
        assert total["total_tokens"] == 15

    def test_usage_accumulates_multiple_calls(self):
        p = GrokProvider()
        p._record_usage("grok-2", {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
        p._record_usage("grok-2-mini", {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300})
        total = p.get_total_usage()
        assert total["prompt_tokens"] == 300
        assert total["completion_tokens"] == 150
        assert total["total_tokens"] == 450
        assert total["cost"] > 0
        assert len(p.get_usage()) == 2

    def test_usage_rounds_cost(self):
        p = GrokProvider()
        p._record_usage("grok-2", {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2})
        total = p.get_total_usage()
        assert total["cost"] == pytest.approx((1 / 1000 * 0.002) + (1 / 1000 * 0.01))

    def test_usage_empty_record(self):
        p = GrokProvider()
        p._record_usage("grok-2", {})
        assert p.get_total_usage()["total_tokens"] == 0

    def test_get_usage_returns_copy(self):
        p = GrokProvider()
        p._record_usage("grok-2", {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
        usage = p.get_usage()
        usage.clear()
        assert len(p.get_usage()) == 1


# ── Grok Provider __init__ overrides ───────────────────────────────────


class TestGrokProviderInit:
    def test_constructor_overrides_api_key(self):
        p = GrokProvider(api_key="custom-key")
        assert p.api_key == "custom-key"

    def test_constructor_overrides_base_url(self):
        p = GrokProvider(base_url="https://custom.x.ai")
        assert p.base_url == "https://custom.x.ai"

    def test_constructor_overrides_both(self):
        p = GrokProvider(api_key="k", base_url="https://k.x.ai")
        assert p.api_key == "k"
        assert p.base_url == "https://k.x.ai"

    def test_constructor_defaults(self):
        p = GrokProvider()
        assert p.name == "grok"
        assert p.default_model == "grok-2"


# ── Grok Fallback Chain ────────────────────────────────────────────────


class TestGrokFallback:
    def test_grok_in_fallback_chains(self):
        assert "grok" in FALLBACK_CHAINS
        assert "openai" in FALLBACK_CHAINS["grok"]
        assert "openrouter" in FALLBACK_CHAINS["grok"]

    def test_grok_uses_chat_with_fallback(self):
        from app.providers import chat_with_fallback

        register_providers()
        grok = get_provider("grok")
        grok.api_key = "test-key"
        with patch.object(grok, "chat", new=AsyncMock(return_value="grok response")):
            import asyncio

            result = asyncio.run(
                chat_with_fallback(
                    messages=[{"role": "user", "content": "hi"}],
                    provider="grok",
                    model="grok-2",
                )
            )
            assert result == "grok response"

    def test_grok_fallback_chain_used_on_failure(self):
        from app.providers import chat_with_fallback

        register_providers()
        grok = get_provider("grok")
        openai = get_provider("openai")
        grok.api_key = "test-key"
        with (
            patch.object(
                grok,
                "chat",
                new=AsyncMock(
                    side_effect=httpx.HTTPStatusError("503", request=MagicMock(), response=MagicMock(status_code=503))
                ),
            ),
            patch.object(openai, "chat", new=AsyncMock(return_value="openai fallback")),
        ):
            import asyncio

            result = asyncio.run(
                chat_with_fallback(
                    messages=[{"role": "user", "content": "hi"}],
                    provider="grok",
                    model="grok-2",
                )
            )
            assert result == "openai fallback"


# ── ProviderManager ────────────────────────────────────────────────────


class TestProviderManager:
    @pytest.fixture(autouse=True)
    def setup(self):
        register_providers()
        self.mgr = ProviderManager()

    def test_get_provider(self):
        p = self.mgr.get_provider("grok")
        assert p is not None
        assert p.name == "grok"

    def test_list_providers(self):
        providers = self.mgr.list_providers()
        assert "grok" in providers
        assert len(providers) >= 8

    def test_count_providers(self):
        assert self.mgr.count_providers() >= 8

    def test_get_fallback_chain(self):
        chain = self.mgr.get_fallback_chain("grok")
        assert "openai" in chain

    def test_set_fallback_chain(self):
        self.mgr.set_fallback_chain("grok", ["ollama"])
        chain = self.mgr.get_fallback_chain("grok")
        assert chain == ["ollama"]

    def test_provider_config(self):
        config = self.mgr.get_provider_config("grok")
        assert config["name"] == "grok"
        assert config["default_model"] == "grok-2"
        assert "fallback_chain" in config

    def test_provider_config_unknown(self):
        config = self.mgr.get_provider_config("nope")
        assert config == {}

    def test_usage_stats(self):
        grok = get_provider("grok")
        grok._record_usage("grok-2", {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
        stats = self.mgr.get_usage_stats()
        assert "grok" in stats
        assert stats["grok"]["total_tokens"] == 15

    def test_usage_stats_empty_provider(self):
        from app.providers.ollama import OllamaProvider

        class NoUsageProvider(OllamaProvider):
            pass

        NoUsageProvider()
        stats = self.mgr.get_usage_stats()
        assert "ollama" in stats

    @pytest.mark.asyncio
    async def test_check_provider_health(self):
        grok = get_provider("grok")
        with patch.object(grok, "check_health", new=AsyncMock(return_value=True)):
            result = await self.mgr.check_provider_health("grok")
            assert result is True

    @pytest.mark.asyncio
    async def test_check_provider_health_not_found(self):
        result = await self.mgr.check_provider_health("nope")
        assert result is False

    @pytest.mark.asyncio
    async def test_chat_with_fallback_through_mgr(self):
        grok = get_provider("grok")
        grok.api_key = "test-key"
        with patch.object(grok, "chat", new=AsyncMock(return_value="mgr response")):
            result = await self.mgr.chat(
                messages=[{"role": "user", "content": "hi"}],
                provider="grok",
                fallback=True,
            )
            assert result == "mgr response"

    @pytest.mark.asyncio
    async def test_chat_without_fallback(self):
        grok = get_provider("grok")
        grok.api_key = "test-key"
        with patch.object(grok, "chat", new=AsyncMock(return_value="direct")):
            result = await self.mgr.chat(
                messages=[{"role": "user", "content": "hi"}],
                provider="grok",
                fallback=False,
                model="grok-2",
            )
            assert result == "direct"

    def test_list_all_models(self):
        import asyncio

        all_models = asyncio.run(self.mgr.list_all_models())
        assert isinstance(all_models, dict)

    def test_list_models_for(self):
        import asyncio

        models = asyncio.run(self.mgr.list_models_for("grok"))
        assert isinstance(models, list)


# ── Grok Plugin Registration ───────────────────────────────────────────


class TestGrokPlugin:
    @pytest.fixture
    def plugin_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider_dir = os.path.join(tmp, "providers", "grok")
            os.makedirs(provider_dir, exist_ok=True)

            manifest = {
                "name": "grok",
                "version": "1.0.0",
                "description": "Grok (xAI) plugin",
                "author": "OpenPaper AI",
                "plugin_type": "provider",
                "entrypoint": "plugin.py",
                "dependencies": [],
                "permissions": ["network"],
                "hooks": ["on_load", "on_unload"],
                "config_schema": {
                    "api_key": {"type": "string"},
                    "base_url": {"type": "string", "default": "https://api.x.ai"},
                },
            }
            with open(os.path.join(provider_dir, "plugin.yaml"), "w") as f:
                yaml.dump(manifest, f)

            plugin_code = """import logging
from typing import AsyncIterator
from app.core.plugin_base import ProviderPlugin

logger = logging.getLogger(__name__)

class GrokPlugin(ProviderPlugin):
    name = "grok"
    version = "1.0.0"
    description = "Grok plugin"

    def __init__(self):
        super().__init__()
        self._provider = None

    async def chat(self, messages, model=None, **kwargs):
        return "grok plugin response"

    async def chat_stream(self, messages, model=None, **kwargs):
        for chunk in ["chunk1", " chunk2"]:
            yield chunk

    async def check_health(self):
        return True

    async def list_models(self):
        return ["grok-2", "grok-2-mini"]
"""
            with open(os.path.join(provider_dir, "plugin.py"), "w") as f:
                f.write(plugin_code)

            yield tmp

    def test_discover_grok_plugin(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        manifests = registry.discover()
        names = [m.name for m in manifests]
        assert "grok" in names

    def test_load_grok_plugin(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        responses = registry.discover_and_load()
        loaded = [r for r in responses if r.name == "grok"]
        assert len(loaded) == 1
        assert loaded[0].status.value == "loaded"

    def test_plugin_chat(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        plugin = registry.get_plugin("grok")
        assert plugin is not None
        import asyncio

        result = asyncio.run(plugin.chat([{"role": "user", "content": "hi"}]))
        assert result == "grok plugin response"

    def test_plugin_check_health(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        plugin = registry.get_plugin("grok")
        assert plugin is not None
        import asyncio

        result = asyncio.run(plugin.check_health())
        assert result is True

    def test_plugin_list_models(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        plugin = registry.get_plugin("grok")
        assert plugin is not None
        import asyncio

        models = asyncio.run(plugin.list_models())
        assert "grok-2" in models
        assert "grok-2-mini" in models

    def test_plugin_enable_disable(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        resp = registry.enable("grok")
        assert resp.status.value == "enabled"
        resp = registry.disable("grok")
        assert resp.status.value == "disabled"

    def test_plugin_sandbox_permission(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        sandbox = registry.get_sandbox("grok")
        assert sandbox is not None
        from app.models.plugin import PluginPermission

        assert sandbox.check_permission(PluginPermission.NETWORK) is True

    def test_unload_grok_plugin(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        assert registry.get_plugin("grok") is not None
        registry.unload("grok")
        assert registry.get_plugin("grok") is None

    def test_plugin_stream(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        plugin = registry.get_plugin("grok")
        import asyncio

        chunks = []

        async def collect():
            async for chunk in plugin.chat_stream([{"role": "user", "content": "hi"}]):
                chunks.append(chunk)

        asyncio.run(collect())
        assert "".join(chunks) == "chunk1 chunk2"
