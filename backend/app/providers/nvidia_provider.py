import json
import httpx
from typing import AsyncGenerator

from app.providers.base import BaseProvider, ProviderConfig, ModelInfo, ProviderStatus


class NVIDIAProvider(BaseProvider):
    provider_name = "nvidia"
    default_model = "nvidia/llama-3.1-nvlm-8b"

    def __init__(self, config: ProviderConfig | None = None):
        super().__init__(config)
        self.models = []
        self._nim_detected = False

    async def is_available(self) -> bool:
        if not self.config.api_key and not self.config.base_url:
            self.status = ProviderStatus.UNCONFIGURED
            return False

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                headers = {}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                resp = await client.get(
                    f"{self.config.base_url}/models",
                    headers=headers,
                )
                available = resp.status_code == 200
                if available:
                    self._nim_detected = True
                    self.status = ProviderStatus.AVAILABLE
                return available
        except Exception:
            self.status = ProviderStatus.UNAVAILABLE
            return False

    def _check_nim_endpoints(self) -> list[str]:
        candidates = [
            self.config.base_url.rstrip("/"),
            self.config.base_url.rstrip("/").replace("/v1", ""),
            "http://localhost:8008",
            "http://localhost:9999",
        ]
        return list(set(candidates))

    async def list_models(self) -> list[ModelInfo]:
        if self.models:
            return self.models

        try:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            endpoints = self._check_nim_endpoints()
            for endpoint in endpoints:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        resp = await client.get(f"{endpoint}/models", headers=headers)
                        if resp.status_code == 200:
                            data = resp.json()
                            models_list = data.get("data", [])
                            if models_list:
                                self.models = [
                                    ModelInfo(
                                        id=m["id"],
                                        provider="nvidia",
                                        name=m.get("id", "NVIDIA Model"),
                                        context_length=m.get("context_length", 131072),
                                        pricing_input_per_1k=0.0,
                                        pricing_output_per_1k=0.0,
                                        capabilities=["chat", "streaming", "code"],
                                    )
                                    for m in models_list
                                ]
                                self._nim_detected = True
                                return self.models
                except Exception:
                    continue

            self.models = [
                ModelInfo(id="nvidia/llama-3.1-nvlm-8b",  provider="nvidia", name="Llama 3.1 NVLM 8B", context_length=131072, pricing_input_per_1k=0.0, pricing_output_per_1k=0.0, capabilities=["chat", "streaming", "vision", "code"]),
                ModelInfo(id="nvidia/mistral-nemo-12b",   provider="nvidia", name="Mistral NeMo 12B",  context_length=131072, pricing_input_per_1k=0.0, pricing_output_per_1k=0.0, capabilities=["chat", "streaming", "code"]),
            ]
        except Exception:
            pass

        return self.models

    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> tuple[str, dict]:
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"] or ""
        usage_data = data.get("usage", {})
        usage = {
            "input_tokens": usage_data.get("prompt_tokens", 0),
            "output_tokens": usage_data.get("completion_tokens", 0),
            "total_tokens": usage_data.get("total_tokens", 0),
        }
        return content, usage

    async def chat_stream(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[tuple[str, dict], None]:
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        final_usage = {}
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line[6:] != "[DONE]":
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                yield delta["content"], {}
                            if chunk.get("usage"):
                                u = chunk["usage"]
                                final_usage = {
                                    "input_tokens": u.get("prompt_tokens", 0),
                                    "output_tokens": u.get("completion_tokens", 0),
                                    "total_tokens": u.get("total_tokens", 0),
                                }
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

        yield "", final_usage
