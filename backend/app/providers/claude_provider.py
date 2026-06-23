import json
import httpx
from typing import AsyncGenerator

from app.providers.base import BaseProvider, ProviderConfig, ModelInfo, ProviderStatus


class ClaudeProvider(BaseProvider):
    provider_name = "claude"
    default_model = "claude-3-5-sonnet-20240620"

    MODEL_MAP = {
        "claude-3-5-sonnet-20240620": ModelInfo(id="claude-3-5-sonnet-20240620", provider="claude", name="Claude 3.5 Sonnet", context_length=200000, pricing_input_per_1k=3.00, pricing_output_per_1k=15.00, capabilities=["chat", "streaming", "vision", "tools"]),
        "claude-3-opus-20240229":     ModelInfo(id="claude-3-opus-20240229",     provider="claude", name="Claude 3 Opus",     context_length=200000, pricing_input_per_1k=15.00, pricing_output_per_1k=75.00, capabilities=["chat", "streaming", "vision", "tools"]),
        "claude-3-haiku-20240307":    ModelInfo(id="claude-3-haiku-20240307",    provider="claude", name="Claude 3 Haiku",    context_length=200000, pricing_input_per_1k=0.25,  pricing_output_per_1k=1.25,  capabilities=["chat", "streaming", "vision", "tools"]),
    }

    def __init__(self, config: ProviderConfig | None = None):
        super().__init__(config)
        self.models = list(self.MODEL_MAP.values())

    async def is_available(self) -> bool:
        if not self.config.api_key:
            self.status = ProviderStatus.UNCONFIGURED
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.config.base_url}/models",
                    headers={
                        "x-api-key": self.config.api_key,
                        "anthropic-version": "2023-06-01",
                    },
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
        system_msg = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system_msg += m["content"] + "\n"
            else:
                filtered.append(m)

        payload = {
            "model": model or self.default_model,
            "messages": filtered,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }
        if system_msg.strip():
            payload["system"] = system_msg.strip()

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.config.base_url}/messages",
                headers={
                    "x-api-key": self.config.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        content = "".join(b.text for b in data.get("content", []) if b.type == "text")
        usage_data = data.get("usage", {})
        usage = {
            "input_tokens": usage_data.get("input_tokens", 0),
            "output_tokens": usage_data.get("output_tokens", 0),
            "total_tokens": usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
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
        system_msg = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system_msg += m["content"] + "\n"
            else:
                filtered.append(m)

        payload = {
            "model": model or self.default_model,
            "messages": filtered,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }
        if system_msg.strip():
            payload["system"] = system_msg.strip()

        input_tokens = 0
        output_tokens = 0

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.config.base_url}/messages",
                headers={
                    "x-api-key": self.config.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            if chunk["type"] == "content_block_delta":
                                delta = chunk.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", ""), {}
                            if chunk["type"] == "message_start":
                                usage = chunk.get("message", {}).get("usage", {})
                                input_tokens = usage.get("input_tokens", 0)
                            if chunk["type"] == "message_delta":
                                usage = chunk.get("usage", {})
                                output_tokens = usage.get("output_tokens", 0)
                        except (json.JSONDecodeError, KeyError):
                            continue

        yield "", {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }
