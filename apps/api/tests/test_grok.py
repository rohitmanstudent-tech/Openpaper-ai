"""Tests for the Grok (xAI) provider module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers import get_provider, get_providers, register_providers
from app.providers.grok import COST_PER_1K_TOKENS, GrokProvider


@pytest.fixture
def grok():
    provider = GrokProvider()
    provider.api_key = "test-key"
    return provider


class TestGrokProvider:
    def test_name_and_default_model(self, grok):
        assert grok.name == "grok"
        assert grok.default_model == "grok-2"

    def test_cost_rates_defined(self):
        assert "grok-2" in COST_PER_1K_TOKENS
        assert "grok-2-mini" in COST_PER_1K_TOKENS
        assert COST_PER_1K_TOKENS["grok-2"]["input"] == 0.00200
        assert COST_PER_1K_TOKENS["grok-2"]["output"] == 0.01000
        assert COST_PER_1K_TOKENS["grok-2-mini"]["input"] == 0.00030
        assert COST_PER_1K_TOKENS["grok-2-mini"]["output"] == 0.00150

    def test_estimate_cost(self, grok):
        cost = grok.estimate_cost("grok-2", 1000, 500)
        expected = (1000 / 1000 * 0.00200) + (500 / 1000 * 0.01000)
        assert cost == pytest.approx(expected)

    def test_estimate_cost_mini(self, grok):
        cost = grok.estimate_cost("grok-2-mini", 2000, 1000)
        expected = (2000 / 1000 * 0.00030) + (1000 / 1000 * 0.00150)
        assert cost == pytest.approx(expected)

    def test_estimate_cost_unknown_model_falls_back(self, grok):
        cost = grok.estimate_cost("unknown-model", 1000, 500)
        expected = (1000 / 1000 * 0.00200) + (500 / 1000 * 0.01000)
        assert cost == pytest.approx(expected)

    def test_headers(self, grok):
        headers = grok._headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-key"

    def test_url(self, grok):
        url = grok._url()
        assert "https://api.x.ai" in url
        assert "/v1/chat/completions" in url

    def test_build_config(self, grok):
        config = grok._build_config(
            temperature=0.8,
            max_tokens=2048,
            top_p=0.95,
            frequency_penalty=0.2,
            presence_penalty=0.1,
        )
        assert config["temperature"] == 0.8
        assert config["max_tokens"] == 2048
        assert config["top_p"] == 0.95
        assert config["frequency_penalty"] == 0.2
        assert config["presence_penalty"] == 0.1

    def test_build_config_empty(self, grok):
        config = grok._build_config()
        assert config == {}

    def test_list_models_fallback(self, grok):
        grok.api_key = ""
        import asyncio

        models = asyncio.run(grok.list_models())
        assert "grok-2" in models
        assert "grok-2-mini" in models

    def test_check_health_no_key(self, grok):
        grok.api_key = ""
        import asyncio

        result = asyncio.run(grok.check_health())
        assert result is False


class TestGrokProviderMocked:
    @patch("httpx.AsyncClient")
    async def test_chat_success(self, mock_client, grok):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "choices": [{"message": {"content": "Hello from Grok!"}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            }
        )
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        result = await grok.chat([{"role": "user", "content": "Hi"}])
        assert result == "Hello from Grok!"

    @patch("httpx.AsyncClient")
    async def test_chat_stream(self, mock_client, grok):
        lines = [
            'data: {"choices":[{"delta":{"content":"Hello"},"index":0}]}',
            'data: {"choices":[{"delta":{"content":" from Grok"},"index":0}]}',
            "data: [DONE]",
        ]

        async def mock_aiter_lines():
            for line in lines:
                yield line

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.aiter_lines = mock_aiter_lines

        mock_stream_cm = MagicMock()
        mock_stream_cm.__aenter__.return_value = mock_resp
        mock_stream_cm.__aexit__.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.stream.return_value = mock_stream_cm
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        chunks = []
        async for chunk in grok.chat_stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)
        assert chunks == ["Hello", " from Grok"]

    @patch("httpx.AsyncClient")
    async def test_chat_stream_usage_tracking(self, mock_client, grok):
        lines = [
            'data: {"choices":[{"delta":{"content":"Hi"},"index":0}]}',
            'data: {"choices":[{"delta":{},"index":0}],"usage":{"prompt_tokens":5,"completion_tokens":3,"total_tokens":8}}',
            "data: [DONE]",
        ]

        async def mock_aiter_lines():
            for line in lines:
                yield line

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.aiter_lines = mock_aiter_lines

        mock_stream_cm = MagicMock()
        mock_stream_cm.__aenter__.return_value = mock_resp
        mock_stream_cm.__aexit__.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.stream.return_value = mock_stream_cm
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        chunks = []
        async for chunk in grok.chat_stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)
        assert chunks == ["Hi"]

    @patch("httpx.AsyncClient")
    async def test_chat_401_error(self, mock_client, grok):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="Grok API key is invalid"):
            await grok.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_chat_402_error(self, mock_client, grok):
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="insufficient balance"):
            await grok.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_chat_429_error(self, mock_client, grok):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="rate limit exceeded"):
            await grok.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_chat_no_choices(self, mock_client, grok):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"choices": []})

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="returned no choices"):
            await grok.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_check_health_success(self, mock_client, grok):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await grok.check_health()
        assert result is True

    @patch("httpx.AsyncClient")
    async def test_check_health_failure(self, mock_client, grok):
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("fail"))

        result = await grok.check_health()
        assert result is False

    @patch("httpx.AsyncClient")
    async def test_list_models_success(self, mock_client, grok):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "data": [
                    {"id": "grok-2"},
                    {"id": "grok-2-mini"},
                    {"id": "grok-vision-beta"},
                ]
            }
        )
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        models = await grok.list_models()
        assert "grok-2" in models
        assert "grok-2-mini" in models
        assert "grok-vision-beta" in models

    @patch("httpx.AsyncClient")
    async def test_list_models_filters_non_grok(self, mock_client, grok):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "data": [
                    {"id": "grok-2"},
                    {"id": "gpt-4"},
                    {"id": "claude-3"},
                ]
            }
        )
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        models = await grok.list_models()
        assert "grok-2" in models
        assert "gpt-4" not in models
        assert "claude-3" not in models


class TestGrokProviderRegistration:
    def test_provider_registered(self):
        register_providers()
        provider = get_provider("grok")
        assert provider is not None
        assert provider.name == "grok"

    def test_provider_in_registry(self):
        register_providers()
        providers = get_providers()
        assert "grok" in providers

    def test_provider_has_required_methods(self):
        provider = GrokProvider()
        assert hasattr(provider, "chat")
        assert hasattr(provider, "chat_stream")
        assert hasattr(provider, "check_health")
        assert hasattr(provider, "list_models")
