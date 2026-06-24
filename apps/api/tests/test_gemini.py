"""Tests for the Gemini provider module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers import get_provider, get_providers, register_providers
from app.providers.gemini import COST_PER_1K_TOKENS, GeminiProvider


@pytest.fixture
def gemini():
    provider = GeminiProvider()
    provider.api_key = "test-key"
    return provider


class TestGeminiProvider:
    def test_name_and_default_model(self, gemini):
        assert gemini.name == "gemini"
        assert gemini.default_model == "gemini-2.5-flash"

    def test_cost_rates_defined(self):
        assert "gemini-2.5-pro" in COST_PER_1K_TOKENS
        assert "gemini-2.5-flash" in COST_PER_1K_TOKENS
        assert COST_PER_1K_TOKENS["gemini-2.5-pro"]["input"] == 0.00125
        assert COST_PER_1K_TOKENS["gemini-2.5-flash"]["input"] == 0.00015

    def test_estimate_cost(self, gemini):
        cost = gemini.estimate_cost("gemini-2.5-flash", 1000, 500)
        expected = (1000 / 1000 * 0.00015) + (500 / 1000 * 0.00060)
        assert cost == pytest.approx(expected)

    def test_estimate_cost_pro_model(self, gemini):
        cost = gemini.estimate_cost("gemini-2.5-pro", 1000, 500)
        expected = (1000 / 1000 * 0.00125) + (500 / 1000 * 0.00500)
        assert cost == pytest.approx(expected)

    def test_estimate_cost_unknown_model_falls_back(self, gemini):
        cost = gemini.estimate_cost("unknown-model", 1000, 500)
        expected = (1000 / 1000 * 0.00015) + (500 / 1000 * 0.00060)
        assert cost == pytest.approx(expected)

    def test_format_messages_converts_system(self, gemini):
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        contents = gemini._format_messages(messages)
        assert len(contents) == 3
        assert contents[0]["role"] == "user"
        assert "[System instruction]" in contents[0]["parts"][0]["text"]
        assert contents[1]["role"] == "user"
        assert contents[1]["parts"][0]["text"] == "Hello"
        assert contents[2]["role"] == "model"
        assert contents[2]["parts"][0]["text"] == "Hi there"

    def test_build_config(self, gemini):
        config = gemini._build_config(temperature=0.7, max_tokens=4096, top_p=0.9)
        assert config["temperature"] == 0.7
        assert config["maxOutputTokens"] == 4096
        assert config["topP"] == 0.9

    def test_build_config_empty(self, gemini):
        config = gemini._build_config()
        assert config == {}

    def test_headers(self, gemini):
        headers = gemini._headers()
        assert headers["Content-Type"] == "application/json"

    def test_url_generation(self, gemini):
        url = gemini._url("gemini-2.5-flash", stream=False)
        assert "gemini-2.5-flash" in url
        assert "generateContent" in url
        headers = gemini._headers()
        assert headers["x-goog-api-key"] == "test-key"

        stream_url = gemini._url("gemini-2.5-pro", stream=True)
        assert "gemini-2.5-pro" in stream_url
        assert "streamGenerateContent" in stream_url

    def test_list_models_fallback(self, gemini):
        gemini.api_key = ""
        import asyncio

        models = asyncio.run(gemini.list_models())
        assert "gemini-2.5-pro" in models
        assert "gemini-2.5-flash" in models

    def test_check_health_no_key(self, gemini):
        gemini.api_key = ""
        import asyncio

        result = asyncio.run(gemini.check_health())
        assert result is False


class TestGeminiProviderMocked:
    @patch("httpx.AsyncClient")
    async def test_chat_success(self, mock_client, gemini):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "candidates": [{"content": {"parts": [{"text": "Hello! How can I help you?"}]}}],
                "usageMetadata": {
                    "promptTokenCount": 10,
                    "candidatesTokenCount": 20,
                    "totalTokenCount": 30,
                },
            }
        )
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        result = await gemini.chat([{"role": "user", "content": "Hi"}])
        assert result == "Hello! How can I help you?"

    @patch("httpx.AsyncClient")
    async def test_chat_stream(self, mock_client, gemini):
        lines = [
            '{"candidates":[{"content":{"parts":[{"text":"Hello"}]}}],"usageMetadata":{"promptTokenCount":5,"candidatesTokenCount":3}}',
            '{"candidates":[{"content":{"parts":[{"text":" world"}]}}]}',
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
        async for chunk in gemini.chat_stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)
        assert chunks == ["Hello", " world"]

    @patch("httpx.AsyncClient")
    async def test_chat_403_error(self, mock_client, gemini):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="Gemini API key is invalid"):
            await gemini.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_chat_429_error(self, mock_client, gemini):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="Gemini rate limit exceeded"):
            await gemini.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_check_health_success(self, mock_client, gemini):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await gemini.check_health()
        assert result is True

    @patch("httpx.AsyncClient")
    async def test_check_health_failure(self, mock_client, gemini):
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("fail"))

        result = await gemini.check_health()
        assert result is False

    @patch("httpx.AsyncClient")
    async def test_list_models_success(self, mock_client, gemini):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "models": [
                    {"name": "models/gemini-2.5-flash"},
                    {"name": "models/gemini-2.5-pro"},
                    {"name": "models/gemini-1.5-pro"},
                ]
            }
        )
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        models = await gemini.list_models()
        assert "gemini-2.5-flash" in models
        assert "gemini-2.5-pro" in models
        assert "gemini-1.5-pro" in models


class TestGeminiProviderRegistration:
    def test_provider_registered(self):
        register_providers()
        provider = get_provider("gemini")
        assert provider is not None
        assert provider.name == "gemini"

    def test_provider_in_registry(self):
        register_providers()
        providers = get_providers()
        assert "gemini" in providers

    def test_provider_has_required_methods(self):
        provider = GeminiProvider()
        assert hasattr(provider, "chat")
        assert hasattr(provider, "chat_stream")
        assert hasattr(provider, "check_health")
        assert hasattr(provider, "list_models")
