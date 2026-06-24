"""Tests for the NVIDIA NIM provider module."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from app.providers import get_provider, get_providers, register_providers
from app.providers.nim import (
    CLOUD_NIM_BASE_URL,
    COST_PER_1K_TOKENS,
    LOCAL_NIM_BASE_URL,
    RTX_OPTIMIZED_MODELS,
    NimProvider,
    detect_gpu,
)


@pytest.fixture
def nim():
    provider = NimProvider()
    provider.api_key = ""
    provider._gpu_info = {"available": False, "gpu_name": "", "is_rtx": False, "cuda_version": "", "vram_gb": 0.0}
    provider._using_cloud = False
    provider.base_url = LOCAL_NIM_BASE_URL
    return provider


class TestDetectGPU:
    @patch("app.providers.nim.shutil.which")
    def test_no_nvidia_smi(self, mock_which):
        mock_which.return_value = None
        result = detect_gpu()
        assert result["available"] is False
        assert result["gpu_name"] == ""

    @patch("app.providers.nim.shutil.which")
    @patch("app.providers.nim.subprocess.check_output")
    def test_rtx_gpu_detected(self, mock_check_output, mock_which):
        mock_which.return_value = "/usr/bin/nvidia-smi"
        mock_check_output.return_value = "NVIDIA GeForce RTX 4090, 24564, 8.9\n"
        result = detect_gpu()
        assert result["available"] is True
        assert "RTX" in result["gpu_name"]
        assert result["is_rtx"] is True
        assert result["vram_gb"] == pytest.approx(24.0, rel=0.1)

    @patch("app.providers.nim.shutil.which")
    @patch("app.providers.nim.subprocess.check_output")
    def test_non_rtx_gpu(self, mock_check_output, mock_which):
        mock_which.return_value = "/usr/bin/nvidia-smi"
        mock_check_output.return_value = "Tesla T4, 15360, 7.5\n"
        result = detect_gpu()
        assert result["available"] is True
        assert result["is_rtx"] is False
        assert result["vram_gb"] == pytest.approx(15.0, rel=0.1)

    @patch("app.providers.nim.shutil.which")
    @patch("app.providers.nim.subprocess.check_output")
    def test_subprocess_failure(self, mock_check_output, mock_which):
        mock_which.return_value = "/usr/bin/nvidia-smi"
        mock_check_output.side_effect = FileNotFoundError
        result = detect_gpu()
        assert result["available"] is False


class TestNimProvider:
    def test_name_and_default_model(self, nim):
        assert nim.name == "nim"
        assert nim.default_model == "meta/llama-3.1-8b-instruct"

    @patch("app.providers.nim.NimProvider.gpu_info", new_callable=PropertyMock)
    def test_local_mode_no_gpu_no_key(self, mock_gpu):
        mock_gpu.return_value = {
            "available": False,
            "gpu_name": "",
            "is_rtx": False,
            "cuda_version": "",
            "vram_gb": 0.0,
        }
        provider = NimProvider()
        provider.api_key = ""
        assert provider.using_cloud is False
        assert provider.base_url == LOCAL_NIM_BASE_URL

    @patch("app.providers.nim.NimProvider.gpu_info", new_callable=PropertyMock)
    def test_cloud_fallback_with_key(self, mock_gpu):
        mock_gpu.return_value = {
            "available": False,
            "gpu_name": "",
            "is_rtx": False,
            "cuda_version": "",
            "vram_gb": 0.0,
        }
        provider = NimProvider()
        provider.api_key = "test-key"
        provider._detect_and_configure()
        assert provider._using_cloud is True
        assert provider.base_url == CLOUD_NIM_BASE_URL

    @patch("app.providers.nim.NimProvider.gpu_info", new_callable=PropertyMock)
    def test_rtx_optimization(self, mock_gpu):
        mock_gpu.return_value = {
            "available": True,
            "gpu_name": "NVIDIA RTX 4090",
            "is_rtx": True,
            "cuda_version": "8.9",
            "vram_gb": 24.0,
        }
        provider = NimProvider()
        provider.api_key = ""
        assert provider.using_cloud is False
        assert provider.base_url == LOCAL_NIM_BASE_URL

    def test_cost_rates_defined(self):
        assert "local" in COST_PER_1K_TOKENS
        assert "cloud" in COST_PER_1K_TOKENS
        assert COST_PER_1K_TOKENS["local"]["input"] == 0.0
        assert COST_PER_1K_TOKENS["cloud"]["input"] == 0.00300
        assert COST_PER_1K_TOKENS["cloud"]["output"] == 0.01500

    def test_estimate_cost_local(self, nim):
        cost = nim.estimate_cost("local", 1000, 500)
        assert cost == 0.0

    def test_estimate_cost_cloud(self, nim):
        cost = nim.estimate_cost("cloud", 1000, 500)
        expected = (1000 / 1000 * 0.00300) + (500 / 1000 * 0.01500)
        assert cost == pytest.approx(expected)

    def test_headers_local(self, nim):
        headers = nim._headers()
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers

    def test_headers_cloud(self, nim):
        nim._using_cloud = True
        nim.api_key = "test-key"
        headers = nim._headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-key"

    def test_url_local(self, nim):
        url = nim._url()
        assert "localhost:8000" in url
        assert "/chat/completions" in url

    def test_url_cloud(self, nim):
        nim._using_cloud = True
        nim.base_url = CLOUD_NIM_BASE_URL
        url = nim._url()
        assert "api.nvcf.nvidia.com" in url
        assert "/chat/completions" in url

    def test_build_config(self, nim):
        config = nim._build_config(temperature=0.5, max_tokens=1024, top_p=0.95)
        assert config["temperature"] == 0.5
        assert config["max_tokens"] == 1024
        assert config["top_p"] == 0.95

    def test_build_config_empty(self, nim):
        config = nim._build_config()
        assert config == {}

    def test_list_models_rtx(self, nim):
        nim._gpu_info = {
            "available": True,
            "gpu_name": "RTX 4090",
            "is_rtx": True,
            "cuda_version": "8.9",
            "vram_gb": 24.0,
        }
        models = nim._list_local_models()
        assert models == RTX_OPTIMIZED_MODELS

    def test_list_models_low_vram(self, nim):
        nim._gpu_info = {
            "available": True,
            "gpu_name": "RTX 3060",
            "is_rtx": True,
            "cuda_version": "8.6",
            "vram_gb": 8.0,
        }
        models = nim._list_local_models()
        assert models == ["meta/llama-3.1-8b-instruct", "mistralai/mistral-7b-instruct-v0.3"]

    def test_list_models_no_gpu(self, nim):
        nim._gpu_info = {"available": False, "gpu_name": "", "is_rtx": False, "cuda_version": "", "vram_gb": 0.0}
        models = nim._list_local_models()
        assert models == ["meta/llama-3.1-8b-instruct"]

    def test_rtx_optimized_models_defined(self):
        assert "meta/llama-3.1-8b-instruct" in RTX_OPTIMIZED_MODELS
        assert "meta/llama-3.1-70b-instruct" in RTX_OPTIMIZED_MODELS
        assert len(RTX_OPTIMIZED_MODELS) >= 4

    def test_check_health_no_local(self, nim):
        import asyncio

        result = asyncio.run(nim.check_health())
        assert result is False


class TestNimProviderMocked:
    @patch("httpx.AsyncClient")
    async def test_chat_success(self, mock_client, nim):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "choices": [{"message": {"content": "Hello from NIM!"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            }
        )
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        result = await nim.chat([{"role": "user", "content": "Hi"}])
        assert result == "Hello from NIM!"

    @patch("httpx.AsyncClient")
    async def test_chat_stream(self, mock_client, nim):
        lines = [
            'data: {"choices":[{"delta":{"content":"Hello"},"index":0}]}',
            'data: {"choices":[{"delta":{"content":" from NIM"},"index":0}]}',
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
        async for chunk in nim.chat_stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)
        assert chunks == ["Hello", " from NIM"]

    @patch("httpx.AsyncClient")
    async def test_chat_401_error(self, mock_client, nim):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="NVIDIA NIM API key is invalid"):
            await nim.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_chat_402_error(self, mock_client, nim):
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="insufficient balance"):
            await nim.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_chat_429_error(self, mock_client, nim):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="rate limit exceeded"):
            await nim.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_chat_no_choices(self, mock_client, nim):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"choices": []})
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        with pytest.raises(RuntimeError, match="returned no choices"):
            await nim.chat([{"role": "user", "content": "Hi"}])

    @patch("httpx.AsyncClient")
    async def test_check_health_success(self, mock_client, nim):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await nim.check_health()
        assert result is True

    @patch("httpx.AsyncClient")
    async def test_check_health_failure(self, mock_client, nim):
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("fail"))

        result = await nim.check_health()
        assert result is False

    @patch("httpx.AsyncClient")
    async def test_list_cloud_models_success(self, mock_client, nim):
        nim._using_cloud = True
        nim.base_url = CLOUD_NIM_BASE_URL
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "data": [
                    {"id": "nvidia/nemotron-4-340b-instruct"},
                    {"id": "meta/llama-3.1-8b-instruct"},
                ]
            }
        )
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        models = await nim.list_models()
        assert "nvidia/nemotron-4-340b-instruct" in models
        assert "meta/llama-3.1-8b-instruct" in models

    @patch("httpx.AsyncClient")
    async def test_chat_stream_usage_tracking(self, mock_client, nim):
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
        async for chunk in nim.chat_stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)
        assert chunks == ["Hi"]


class TestNimProviderRegistration:
    def test_provider_registered(self):
        register_providers()
        provider = get_provider("nim")
        assert provider is not None
        assert provider.name == "nim"

    def test_provider_in_registry(self):
        register_providers()
        providers = get_providers()
        assert "nim" in providers

    def test_provider_has_required_methods(self):
        provider = NimProvider()
        assert hasattr(provider, "chat")
        assert hasattr(provider, "chat_stream")
        assert hasattr(provider, "check_health")
        assert hasattr(provider, "list_models")
