import json
import httpx
from typing import AsyncGenerator

from app.providers.base import BaseProvider, ProviderConfig, ModelInfo, ProviderStatus


class GrokProvider(BaseProvider):
    provider_name = "grok"
    default_model = "grok-2"

    def __init__(self, config: ProviderConfig | None = None):
        super().__init__(config)
        self.models = [
            ModelInfo(id="grok-2",       provider="grok", name="Grok 2",     context_length=131072, pricing_input_per_1k=2.00, pricing_output_per_1k=10.00, capabilities=["chat", "streaming", "code", "reasoning"]),
            ModelInfo(id="grok-2-mini",  provider="grok", name="Grok 2 Mini", context_length=131072, pricing_input_per_1k=0.10, pricing_output_per_1k=0.50,  capabilities=["chat", "streaming", "code"]),
        ]

    async def is_available(self) -> bool:
        if not self.config.api_key:
            self.status = ProviderStatus.UNCONFIGURED
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.config.base_url}/models",
                    headers={"Authorization": f"Bearer {self.config.api_key}"},
                )
                return resp.status_code == 200
        except Exception:
            self.status = ProviderStatus.UNAVAILABLE
            return False

    async def list_models(self) -> list[ModelInfo]:
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

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
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

        final_usage = {}
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
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
