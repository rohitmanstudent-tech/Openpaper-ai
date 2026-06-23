"""Tests for DeepSeek provider fallback, plugin registration, and resilience."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import yaml

from app.core.plugin_registry import PluginRegistry, set_plugin_registry
from app.providers import (
    FALLBACK_CHAINS,
    chat_stream_with_fallback,
    chat_with_fallback,
    get_fallback_chain,
    get_provider,
    register_providers,
    set_fallback_chain,
)

# ── Fallback Chain Configuration ───────────────────────────────────────


class TestFallbackConfig:
    def test_default_chains_defined(self):
        assert "deepseek" in FALLBACK_CHAINS
        assert "grok" in FALLBACK_CHAINS
        assert "nim" in FALLBACK_CHAINS
        assert "gemini" in FALLBACK_CHAINS
        assert "openrouter" in FALLBACK_CHAINS
        assert "claude" in FALLBACK_CHAINS
        assert "ollama" in FALLBACK_CHAINS

    def test_deepseek_fallbacks(self):
        chain = get_fallback_chain("deepseek")
        assert "openai" in chain
        assert "openrouter" in chain

    def test_nim_fallbacks(self):
        chain = get_fallback_chain("nim")
        assert "openai" in chain
        assert len(chain) == 1

    def test_ollama_no_fallbacks(self):
        chain = get_fallback_chain("ollama")
        assert chain == []

    def test_unknown_provider_no_fallbacks(self):
        chain = get_fallback_chain("nonexistent")
        assert chain == []

    def test_set_fallback_chain(self):
        set_fallback_chain("test_provider", ["openai", "deepseek"])
        chain = get_fallback_chain("test_provider")
        assert chain == ["openai", "deepseek"]


# ── Fallthrough Error Detection ────────────────────────────────────────


class TestFallthroughDetection:
    def test_http_500_is_fallthrough(self):
        from app.providers import _is_fallthrough_error
        response = MagicMock(spec=httpx.Response)
        response.status_code = 503
        error = httpx.HTTPStatusError("503", request=MagicMock(), response=response)
        assert _is_fallthrough_error(error) is True

    def test_http_400_not_fallthrough(self):
        from app.providers import _is_fallthrough_error
        response = MagicMock(spec=httpx.Response)
        response.status_code = 401
        error = httpx.HTTPStatusError("401", request=MagicMock(), response=response)
        assert _is_fallthrough_error(error) is False

    def test_timeout_is_fallthrough(self):
        from app.providers import _is_fallthrough_error
        error = httpx.TimeoutException("timeout")
        assert _is_fallthrough_error(error) is True

    def test_connect_error_is_fallthrough(self):
        from app.providers import _is_fallthrough_error
        error = httpx.ConnectError("connection refused")
        assert _is_fallthrough_error(error) is True

    def test_network_error_is_fallthrough(self):
        from app.providers import _is_fallthrough_error
        error = httpx.NetworkError("eof")
        assert _is_fallthrough_error(error) is True

    def test_runtime_error_service_unavailable_is_fallthrough(self):
        from app.providers import _is_fallthrough_error
        error = RuntimeError("service unavailable")
        assert _is_fallthrough_error(error) is True

    def test_runtime_error_invalid_key_not_fallthrough(self):
        from app.providers import _is_fallthrough_error
        error = RuntimeError("API key is invalid")
        assert _is_fallthrough_error(error) is False


# ── chat_with_fallback ─────────────────────────────────────────────────


class TestChatWithFallback:
    @pytest.fixture(autouse=True)
    def setup(self):
        register_providers()

    @pytest.mark.asyncio
    async def test_primary_succeeds(self):
        deepseek = get_provider("deepseek")
        deepseek.api_key = "test-key"
        with patch.object(deepseek, "chat", new=AsyncMock(return_value="primary response")):
            result = await chat_with_fallback(
                messages=[{"role": "user", "content": "hi"}],
                provider="deepseek",
                model="deepseek-chat",
            )
            assert result == "primary response"

    @pytest.mark.asyncio
    async def test_primary_fails_500_falls_to_openai(self):
        deepseek = get_provider("deepseek")
        openai = get_provider("openai")
        deepseek.api_key = "test-key"
        with (
            patch.object(deepseek, "chat", new=AsyncMock(side_effect=httpx.HTTPStatusError("500", request=MagicMock(), response=MagicMock(status_code=503)))),
            patch.object(openai, "chat", new=AsyncMock(return_value="openai response")),
        ):
            result = await chat_with_fallback(
                messages=[{"role": "user", "content": "hi"}],
                provider="deepseek",
                model="deepseek-chat",
            )
            assert result == "openai response"

    @pytest.mark.asyncio
    async def test_primary_timeout_falls_to_openrouter(self):
        deepseek = get_provider("deepseek")
        openai = get_provider("openai")
        openrouter = get_provider("openrouter")
        deepseek.api_key = "test-key"
        with (
            patch.object(deepseek, "chat", new=AsyncMock(side_effect=httpx.TimeoutException("timeout"))),
            patch.object(openai, "chat", new=AsyncMock(side_effect=httpx.HTTPStatusError("503", request=MagicMock(), response=MagicMock(status_code=503)))),
            patch.object(openrouter, "chat", new=AsyncMock(return_value="openrouter response")),
        ):
            result = await chat_with_fallback(
                messages=[{"role": "user", "content": "hi"}],
                provider="deepseek",
                model="deepseek-chat",
            )
            assert result == "openrouter response"

    @pytest.mark.asyncio
    async def test_all_fail_raises(self):
        deepseek = get_provider("deepseek")
        openai = get_provider("openai")
        openrouter = get_provider("openrouter")
        deepseek.api_key = "test-key"
        with (
            patch.object(deepseek, "chat", new=AsyncMock(side_effect=httpx.HTTPStatusError("503", request=MagicMock(), response=MagicMock(status_code=503)))),
            patch.object(openai, "chat", new=AsyncMock(side_effect=httpx.TimeoutException("timeout"))),
            patch.object(openrouter, "chat", new=AsyncMock(side_effect=httpx.ConnectError("refused"))),
        ):
            with pytest.raises(httpx.ConnectError):
                await chat_with_fallback(
                    messages=[{"role": "user", "content": "hi"}],
                    provider="deepseek",
                    model="deepseek-chat",
                )

    @pytest.mark.asyncio
    async def test_auth_error_does_not_fallthrough(self):
        deepseek = get_provider("deepseek")
        deepseek.api_key = "test-key"
        with patch.object(deepseek, "chat", new=AsyncMock(side_effect=RuntimeError("API key is invalid"))):
            with pytest.raises(RuntimeError, match="API key is invalid"):
                await chat_with_fallback(
                    messages=[{"role": "user", "content": "hi"}],
                    provider="deepseek",
                    model="deepseek-chat",
                )

    @pytest.mark.asyncio
    async def test_ollama_no_fallback_raises_immediately(self):
        ollama = get_provider("ollama")
        with patch.object(ollama, "chat", new=AsyncMock(side_effect=httpx.HTTPStatusError("503", request=MagicMock(), response=MagicMock(status_code=503)))):
            with pytest.raises(httpx.HTTPStatusError):
                await chat_with_fallback(
                    messages=[{"role": "user", "content": "hi"}],
                    provider="ollama",
                    model="llama3.1",
                )


# ── chat_stream_with_fallback ──────────────────────────────────────────


class TestChatStreamWithFallback:
    @pytest.fixture(autouse=True)
    def setup(self):
        register_providers()

    @pytest.mark.asyncio
    async def test_primary_stream_succeeds(self):
        deepseek = get_provider("deepseek")
        deepseek.api_key = "test-key"

        async def fake_stream(_messages, **kwargs):
            for chunk in ["hello ", "world"]:
                yield chunk

        with patch.object(deepseek, "chat_stream", new=fake_stream):
            chunks = []
            async for chunk in chat_stream_with_fallback(
                messages=[{"role": "user", "content": "hi"}],
                provider="deepseek",
                model="deepseek-chat",
            ):
                chunks.append(chunk)
            assert "".join(chunks) == "hello world"

    @pytest.mark.asyncio
    async def test_primary_stream_fails_falls_to_openai(self):
        deepseek = get_provider("deepseek")
        openai = get_provider("openai")
        deepseek.api_key = "test-key"

        async def fake_deepseek_stream(_messages, **kwargs):
            raise httpx.HTTPStatusError("503", request=MagicMock(), response=MagicMock(status_code=503))
            yield  # pragma: no cover

        async def fake_openai_stream(_messages, **kwargs):
            for chunk in ["openai ", "response"]:
                yield chunk

        with (
            patch.object(deepseek, "chat_stream", new=fake_deepseek_stream),
            patch.object(openai, "chat_stream", new=fake_openai_stream),
        ):
            chunks = []
            async for chunk in chat_stream_with_fallback(
                messages=[{"role": "user", "content": "hi"}],
                provider="deepseek",
                model="deepseek-chat",
            ):
                chunks.append(chunk)
            assert "".join(chunks) == "openai response"

    @pytest.mark.asyncio
    async def test_stream_all_fail_raises(self):
        deepseek = get_provider("deepseek")
        openai = get_provider("openai")
        openrouter = get_provider("openrouter")
        deepseek.api_key = "test-key"

        async def fail_503(_m, **kw):
            raise httpx.HTTPStatusError("503", request=MagicMock(), response=MagicMock(status_code=503))
            yield

        async def fail_timeout(_m, **kw):
            raise httpx.TimeoutException("timeout")
            yield

        async def fail_connect(_m, **kw):
            raise httpx.ConnectError("refused")
            yield

        with (
            patch.object(deepseek, "chat_stream", new=fail_503),
            patch.object(openai, "chat_stream", new=fail_timeout),
            patch.object(openrouter, "chat_stream", new=fail_connect),pytest.raises(httpx.ConnectError)
        ):
            async for _ in chat_stream_with_fallback(
                messages=[{"role": "user", "content": "hi"}],
                provider="deepseek",
                model="deepseek-chat",
            ):
                pass


# ── Plugin Registration ────────────────────────────────────────────────


class TestDeepSeekPlugin:
    @pytest.fixture
    def plugin_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider_dir = os.path.join(tmp, "providers", "deepseek")
            os.makedirs(provider_dir, exist_ok=True)

            manifest = {
                "name": "deepseek",
                "version": "1.0.0",
                "description": "DeepSeek Chat & Reasoner plugin",
                "author": "OpenPaper AI",
                "plugin_type": "provider",
                "entrypoint": "plugin.py",
                "dependencies": [],
                "permissions": ["network"],
                "hooks": ["on_load", "on_unload"],
                "config_schema": {
                    "api_key": {"type": "string"},
                    "base_url": {"type": "string", "default": "https://api.deepseek.com"},
                },
            }
            with open(os.path.join(provider_dir, "plugin.yaml"), "w") as f:
                yaml.dump(manifest, f)

            plugin_code = '''import logging
from typing import AsyncIterator
from app.core.plugin_base import ProviderPlugin

logger = logging.getLogger(__name__)

class DeepSeekPlugin(ProviderPlugin):
    name = "deepseek"
    version = "1.0.0"
    description = "DeepSeek plugin"

    def __init__(self):
        super().__init__()
        self._provider = None

    async def chat(self, messages, model=None, **kwargs):
        return "plugin response"

    async def chat_stream(self, messages, model=None, **kwargs):
        for chunk in ["chunk1", " chunk2"]:
            yield chunk

    async def check_health(self):
        return True

    async def list_models(self):
        return ["deepseek-chat", "deepseek-reasoner"]
'''
            with open(os.path.join(provider_dir, "plugin.py"), "w") as f:
                f.write(plugin_code)

            yield tmp

    def test_discover_deepseek_plugin(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        manifests = registry.discover()
        names = [m.name for m in manifests]
        assert "deepseek" in names

    def test_load_deepseek_plugin(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        responses = registry.discover_and_load()
        loaded = [r for r in responses if r.name == "deepseek"]
        assert len(loaded) == 1
        assert loaded[0].status.value == "loaded"

    def test_plugin_chat(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        plugin = registry.get_plugin("deepseek")
        assert plugin is not None
        import asyncio
        result = asyncio.run(plugin.chat([{"role": "user", "content": "hi"}]))
        assert result == "plugin response"

    def test_plugin_check_health(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        plugin = registry.get_plugin("deepseek")
        assert plugin is not None
        import asyncio
        result = asyncio.run(plugin.check_health())
        assert result is True

    def test_plugin_list_models(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        plugin = registry.get_plugin("deepseek")
        assert plugin is not None
        import asyncio
        models = asyncio.run(plugin.list_models())
        assert "deepseek-chat" in models
        assert "deepseek-reasoner" in models

    def test_plugin_enable_disable(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        resp = registry.enable("deepseek")
        assert resp.status.value == "enabled"
        resp = registry.disable("deepseek")
        assert resp.status.value == "disabled"

    def test_plugin_sandbox_permission(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        sandbox = registry.get_sandbox("deepseek")
        assert sandbox is not None
        from app.models.plugin import PluginPermission
        assert sandbox.check_permission(PluginPermission.NETWORK) is True
        assert sandbox.check_permission(PluginPermission.MEMORY_READ) is False

    def test_unload_deepseek_plugin(self, plugin_dir):
        set_plugin_registry(None)
        registry = PluginRegistry(base_dir=plugin_dir)
        registry.discover_and_load()
        assert registry.get_plugin("deepseek") is not None
        registry.unload("deepseek")
        assert registry.get_plugin("deepseek") is None
