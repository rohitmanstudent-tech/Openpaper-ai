"""Tests for NIM plugin, usage tracking, fallback, and ProviderManager."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import httpx
import pytest
import yaml

from app.core.plugin_registry import PluginRegistry, set_plugin_registry
from app.providers import FALLBACK_CHAINS, get_provider, register_providers
from app.providers.manager import ProviderManager
from app.providers.nim import CLOUD_NIM_BASE_URL, NimProvider

# ── Usage Tracking ─────────────────────────────────────────────────────


class TestNimUsageTracking:
    def test_usage_starts_empty(self):
        p = NimProvider()
        assert p.get_usage() == []
        assert p.get_total_usage()["total_tokens"] == 0
        assert p.get_total_usage()["cost"] == 0

    def test_usage_accumulates_local(self):
        p = NimProvider()
        p._record_usage("local", {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
        total = p.get_total_usage()
        assert total["prompt_tokens"] == 100
        assert total["completion_tokens"] == 50
        assert total["total_tokens"] == 150
        assert total["cost"] == 0.0

    def test_usage_accumulates_cloud(self):
        p = NimProvider()
        p._record_usage("cloud", {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
        total = p.get_total_usage()
        assert total["cost"] > 0

    def test_usage_multiple_calls(self):
        p = NimProvider()
        p._record_usage("local", {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
        p._record_usage("cloud", {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300})
        total = p.get_total_usage()
        assert total["prompt_tokens"] == 210
        assert total["completion_tokens"] == 105
        assert total["total_tokens"] == 315

    def test_usage_empty_record(self):
        p = NimProvider()
        p._record_usage("local", {})
        assert p.get_total_usage()["total_tokens"] == 0

    def test_get_usage_returns_copy(self):
        p = NimProvider()
        p._record_usage("local", {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8})
        usage = p.get_usage()
        usage.clear()
        assert len(p.get_usage()) == 1


# ── Constructor Overrides ──────────────────────────────────────────────


class TestNimConstructorOverrides:
    @patch("app.providers.nim.NimProvider.gpu_info", new_callable=PropertyMock)
    def test_overrides_api_key(self, mock_gpu):
        mock_gpu.return_value = {
            "available": False,
            "gpu_name": "",
            "is_rtx": False,
            "cuda_version": "",
            "vram_gb": 0.0,
        }
        p = NimProvider(api_key="custom-key")
        assert p.api_key == "custom-key"

    @patch("app.providers.nim.NimProvider.gpu_info", new_callable=PropertyMock)
    def test_overrides_base_url(self, mock_gpu):
        mock_gpu.return_value = {
            "available": False,
            "gpu_name": "",
            "is_rtx": False,
            "cuda_version": "",
            "vram_gb": 0.0,
        }
        p = NimProvider(base_url="http://custom:8080")
        assert p.base_url == "http://custom:8080"

    @patch("app.providers.nim.NimProvider.gpu_info", new_callable=PropertyMock)
    def test_overrides_both(self, mock_gpu):
        mock_gpu.return_value = {
            "available": True,
            "gpu_name": "NVIDIA RTX 4090",
            "is_rtx": True,
            "cuda_version": "8.9",
            "vram_gb": 24.0,
        }
        p = NimProvider(api_key="k", base_url="http://k:8080")
        assert p.api_key == "k"
        assert p.base_url == "http://k:8080"

    @patch("app.providers.nim.NimProvider.gpu_info", new_callable=PropertyMock)
    def test_api_key_triggers_cloud_without_gpu(self, mock_gpu):
        mock_gpu.return_value = {
            "available": False,
            "gpu_name": "",
            "is_rtx": False,
            "cuda_version": "",
            "vram_gb": 0.0,
        }
        p = NimProvider(api_key="cloud-key")
        assert p.api_key == "cloud-key"
        assert p._using_cloud is True
        assert CLOUD_NIM_BASE_URL in p.base_url

    @patch("app.providers.nim.NimProvider.gpu_info", new_callable=PropertyMock)
    def test_name_and_default_model(self, mock_gpu):
        mock_gpu.return_value = {
            "available": False,
            "gpu_name": "",
            "is_rtx": False,
            "cuda_version": "",
            "vram_gb": 0.0,
        }
        p = NimProvider()
        assert p.name == "nim"
        assert p.default_model == "meta/llama-3.1-8b-instruct"


# ── Fallback Chain ─────────────────────────────────────────────────────


class TestNimFallback:
    def test_nim_in_fallback_chains(self):
        assert "nim" in FALLBACK_CHAINS
        assert "openai" in FALLBACK_CHAINS["nim"]

    def test_nim_fallback_chain_used_on_failure(self):
        from app.providers import chat_with_fallback

        register_providers()
        nim = get_provider("nim")
        openai = get_provider("openai")
        nim.api_key = "test-key"
        with (
            patch.object(
                nim,
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
                    provider="nim",
                    model="meta/llama-3.1-8b-instruct",
                )
            )
            assert result == "openai fallback"

    def test_nim_uses_chat_with_fallback(self):
        from app.providers import chat_with_fallback

        register_providers()
        nim = get_provider("nim")
        nim.api_key = ""
        with patch.object(nim, "chat", new=AsyncMock(return_value="nim response")):
            import asyncio

            result = asyncio.run(
                chat_with_fallback(
                    messages=[{"role": "user", "content": "hi"}],
                    provider="nim",
                    model="meta/llama-3.1-8b-instruct",
                )
            )
            assert result == "nim response"


# ── ProviderManager Integration ────────────────────────────────────────


class TestNimProviderManager:
    @pytest.fixture(autouse=True)
    def setup(self):
        register_providers()
        self.mgr = ProviderManager()

    def test_get_provider(self):
        p = self.mgr.get_provider("nim")
        assert p is not None
        assert p.name == "nim"

    def test_provider_config(self):
        config = self.mgr.get_provider_config("nim")
        assert config["name"] == "nim"
        assert config["default_model"] == "meta/llama-3.1-8b-instruct"
        assert "fallback_chain" in config
        assert "openai" in config["fallback_chain"]

    def test_provider_config_unknown(self):
        config = self.mgr.get_provider_config("nope")
        assert config == {}

    def test_usage_stats(self):
        nim = get_provider("nim")
        nim._record_usage("local", {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75})
        stats = self.mgr.get_usage_stats()
        assert "nim" in stats
        assert stats["nim"]["total_tokens"] == 75

    @pytest.mark.asyncio
    async def test_check_provider_health(self):
        nim = get_provider("nim")
        with patch.object(nim, "check_health", new=AsyncMock(return_value=True)):
            result = await self.mgr.check_provider_health("nim")
            assert result is True

    @pytest.mark.asyncio
    async def test_chat_through_manager(self):
        nim = get_provider("nim")
        nim.api_key = ""
        with patch.object(nim, "chat", new=AsyncMock(return_value="mgr response")):
            result = await self.mgr.chat(
                messages=[{"role": "user", "content": "hi"}],
                provider="nim",
                fallback=False,
            )
            assert result == "mgr response"

    @pytest.mark.asyncio
    async def test_chat_with_fallback_through_manager(self):
        nim = get_provider("nim")
        nim.api_key = ""
        with patch.object(nim, "chat", new=AsyncMock(return_value="fallback response")):
            result = await self.mgr.chat(
                messages=[{"role": "user", "content": "hi"}],
                provider="nim",
                fallback=True,
            )
            assert result == "fallback response"

    def test_list_models_for(self):
        import asyncio

        models = asyncio.run(self.mgr.list_models_for("nim"))
        assert isinstance(models, list)

    def test_nim_in_all_providers(self):
        providers = self.mgr.list_providers()
        assert "nim" in providers

    def test_count_providers(self):
        assert self.mgr.count_providers() >= 8

    def test_set_fallback_chain(self):
        self.mgr.set_fallback_chain("nim", ["deepseek"])
        chain = self.mgr.get_fallback_chain("nim")
        assert chain == ["deepseek"]


# ── NIM Plugin Registration ────────────────────────────────────────────


class TestNimPlugin:
    @pytest.fixture
    def plugin_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider_dir = os.path.join(tmp, "providers", "nim")
            os.makedirs(provider_dir, exist_ok=True)

            manifest = {
                "name": "nim",
                "version": "1.0.0",
                "description": "NVIDIA NIM plugin",
                "author": "OpenPaper AI",
                "plugin_type": "provider",
                "entrypoint": "plugin.py",
                "dependencies": [],
                "permissions": ["network"],
                "hooks": ["on_load", "on_unload"],
                "config_schema": {
                    "api_key": {"type": "string"},
                    "base_url": {"type": "string", "default": "http://localhost:8000"},
                },
            }
            with open(os.path.join(provider_dir, "plugin.yaml"), "w") as f:
                yaml.dump(manifest, f)

            plugin_code = """import logging
from typing import AsyncIterator
from app.core.plugin_base import ProviderPlugin

logger = logging.getLogger(__name__)

class NimPlugin(ProviderPlugin):
    name = "nim"
    version = "1.0.0"
    description = "NIM plugin"

    def __init__(self):
        super().__init__()
        self._gpu = False

    async def chat(self, messages, model=None, **kwargs):
        return "nim plugin response"

    async def chat_stream(self, messages, model=None, **kwargs):
        for chunk in ["chunk1", " chunk2"]:
            yield chunk

    async def check_health(self):
        return True

    async def list_models(self):
        return ["meta/llama-3.1-8b-instruct", "meta/llama-3.1-70b-instruct"]
"""
            with open(os.path.join(provider_dir, "plugin.py"), "w") as f:
                f.write(plugin_code)

            yield tmp

    def test_discover_nim_plugin(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        manifests = registry.discover()
        names = [m.name for m in manifests]
        assert "nim" in names

    def test_load_nim_plugin(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        responses = registry.discover_and_load()
        loaded = [r for r in responses if r.name == "nim"]
        assert len(loaded) == 1
        assert loaded[0].status.value == "loaded"

    def test_plugin_chat(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        plugin = registry.get_plugin("nim")
        assert plugin is not None
        import asyncio

        result = asyncio.run(plugin.chat([{"role": "user", "content": "hi"}]))
        assert result == "nim plugin response"

    def test_plugin_check_health(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        plugin = registry.get_plugin("nim")
        assert plugin is not None
        import asyncio

        result = asyncio.run(plugin.check_health())
        assert result is True

    def test_plugin_list_models(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        plugin = registry.get_plugin("nim")
        assert plugin is not None
        import asyncio

        models = asyncio.run(plugin.list_models())
        assert "meta/llama-3.1-8b-instruct" in models
        assert "meta/llama-3.1-70b-instruct" in models

    def test_plugin_enable_disable(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        resp = registry.enable("nim")
        assert resp.status.value == "enabled"
        resp = registry.disable("nim")
        assert resp.status.value == "disabled"

    def test_plugin_sandbox_permission(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        sandbox = registry.get_sandbox("nim")
        assert sandbox is not None
        from app.models.plugin import PluginPermission

        assert sandbox.check_permission(PluginPermission.NETWORK) is True

    def test_unload_nim_plugin(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        assert registry.get_plugin("nim") is not None
        registry.unload("nim")
        assert registry.get_plugin("nim") is None

    def test_plugin_stream(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        plugin = registry.get_plugin("nim")
        import asyncio

        chunks = []

        async def collect():
            async for chunk in plugin.chat_stream([{"role": "user", "content": "hi"}]):
                chunks.append(chunk)

        asyncio.run(collect())
        assert "".join(chunks) == "chunk1 chunk2"
