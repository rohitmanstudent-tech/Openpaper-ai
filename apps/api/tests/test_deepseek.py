"""Tests for the DeepSeek provider module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers import get_provider, get_providers, register_providers
from app.providers.deepseek import COST_PER_1K_TOKENS, DeepSeekProvider


@pytest.fixture
def deepseek():
    provider = DeepSeekProvider()
    provider.api_key = "test-key"
    return provider


class TestDeepSeekProvider:
    def test_name_and_default_model(self, deepseek):
        assert deepseek.name == "deepseek"
        assert deepseek.default_model == "deepseek-chat"

    def test_cost_rates_defined(self):
        assert "deepseek-chat" in COST_PER_1K_TOKENS
        assert "deepseek-reasoner" in COST_PER_1K_TOKENS
        assert COST_PER_1K_TOKENS["deepseek-chat"]["input"] == 0.00027
        assert COST_PER_1K_TOKENS["deepseek-chat"]["output"] == 0.00110
        assert COST_PER_1K_TOKENS["deepseek-reasoner"]["input"] == 0.00055
        assert COST_PER_1K_TOKENS["deepseek-reasoner"]["output"] == 0.00219

    def test_estimate_cost(self, deepseek):
        cost = deepseek.estimate_cost("deepseek-chat", 1000, 500)
        expected = (1000 / 1000 * 0.00027) + (500 / 1000 * 0.00110)
        assert cost == pytest.approx(expected)

    def test_estimate_cost_reasoner(self, deepseek):
        cost = deepseek.estimate_cost("deepseek-reasoner", 2000, 1000)
        expected = (2000 / 1000 * 0.00055) + (1000 / 1000 * 0.00219)
        assert cost == pytest.approx(expected)

    def test_estimate_cost_unknown_model_falls_back(self, deepseek):
        cost = deepseek.estimate_cost("unknown-model", 1000, 500)
        expected = (1000 / 1000 * 0.00027) + (500 / 1000 * 0.00110)
        assert cost == pytest.approx(expected)

    def test_headers(self, deepseek):
        headers = deepseek._headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-key"

    def test_url(self, deepseek):
        url = deepseek._url()
        assert "https://api.deepseek.com" in url
        assert "/v1/chat/completions" in url

    def test_build_config(self, deepseek):
        config = deepseek._build_config(
            temperature=0.7,
            max_tokens=4096,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.3,
        )
        assert config["temperature"] == 0.7
        assert config["max_tokens"] == 4096
        assert config["top_p"] == 0.9
        assert config["frequency_penalty"] == 0.5
        assert config["presence_penalty"] == 0.3

    def test_build_config_empty(self, deepseek):
        config = deepseek._build_config()
        assert config == {}

    def test_list_models_fallback(self, deepseek):
        deepseek.api_key = ""
        import asyncio

        models = asyncio.run(deepseek.list_models())
        assert "deepseek-chat" in models
        assert "deepseek-reasoner" in models

    def test_check_health_no_key(self, deepseek):
        deepseek.api_key = ""
        import asyncio

        result = asyncio.run(deepseek.check_health())
        assert result is False


class TestDeepSeekProviderMocked:
    @patch("httpx.AsyncClient")
    async def test_chat_success(self, mock_client, deepseek):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "choices": [{"message": {"content": "Hello! How can I help you?"}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            }
        )
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        result = await deepseek.chat([{"role": "user", "content": "Hi"}])
        assert result == "Hello! How can I help you?"

    @patch("httpx.AsyncClient")
    async def test_chat_stream(self, mock_client, deepseek):
        lines = [
            'data: {"choices":[{"delta":{"content":"Hello"},"index":0}]}',
            'data: {"choices":[{"delta":{"content":" world"},"index":0}]}',
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
        async for chunk in deepseek.chat_stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)
        assert chunks == ["Hello", " world"]

    @patch("httpx.AsyncClient")
    async def test_chat_stream_usage_in_last_chunk(self, mock_client, deepseek):
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
        async for chunk in deepseek.chat_stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)
        assert chunks == ["Hi"]

    @patch("httpx.AsyncClient")
    async def test_chat_401_error(self, mock_client, deepseek):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="DeepSeek API key is invalid"):
            await deepseek.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_chat_402_error(self, mock_client, deepseek):
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="insufficient balance"):
            await deepseek.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_chat_429_error(self, mock_client, deepseek):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="rate limit exceeded"):
            await deepseek.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_chat_no_choices(self, mock_client, deepseek):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"choices": []})

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="returned no choices"):
            await deepseek.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_check_health_success(self, mock_client, deepseek):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await deepseek.check_health()
        assert result is True

    @patch("httpx.AsyncClient")
    async def test_check_health_failure(self, mock_client, deepseek):
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("fail"))

        result = await deepseek.check_health()
        assert result is False

    @patch("httpx.AsyncClient")
    async def test_list_models_success(self, mock_client, deepseek):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "data": [
                    {"id": "deepseek-chat"},
                    {"id": "deepseek-reasoner"},
                ]
            }
        )
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        models = await deepseek.list_models()
        assert "deepseek-chat" in models
        assert "deepseek-reasoner" in models

    @patch("httpx.AsyncClient")
    async def test_list_models_no_deepseek_models(self, mock_client, deepseek):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "data": [
                    {"id": "gpt-4"},
                    {"id": "claude-3"},
                ]
            }
        )
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        models = await deepseek.list_models()
        assert models == []


class TestDeepSeekProviderRegistration:
    def test_provider_registered(self):
        register_providers()
        provider = get_provider("deepseek")
        assert provider is not None
        assert provider.name == "deepseek"

    def test_provider_in_registry(self):
        register_providers()
        providers = get_providers()
        assert "deepseek" in providers

    def test_provider_has_required_methods(self):
        provider = DeepSeekProvider()
        assert hasattr(provider, "chat")
        assert hasattr(provider, "chat_stream")
        assert hasattr(provider, "check_health")
        assert hasattr(provider, "list_models")
