import httpx
from typing import AsyncGenerator

from app.providers.base import BaseProvider, ProviderConfig, ModelInfo, ProviderStatus


class OpenAIProvider(BaseProvider):
    provider_name = "openai"
    default_model = "gpt-4o"

    MODEL_MAP = {
        "gpt-4o":          ModelInfo(id="gpt-4o",          provider="openai", name="GPT-4o",           context_length=128000, pricing_input_per_1k=5.00,  pricing_output_per_1k=15.00, capabilities=["chat", "streaming", "vision", "tools", "json_mode"]),
        "gpt-4o-mini":     ModelInfo(id="gpt-4o-mini",     provider="openai", name="GPT-4o Mini",      context_length=128000, pricing_input_per_1k=0.15,  pricing_output_per_1k=0.60,  capabilities=["chat", "streaming", "vision", "tools", "json_mode"]),
        "gpt-4-turbo":     ModelInfo(id="gpt-4-turbo",     provider="openai", name="GPT-4 Turbo",      context_length=128000, pricing_input_per_1k=10.00, pricing_output_per_1k=30.00, capabilities=["chat", "streaming", "vision", "tools"]),
        "gpt-3.5-turbo":   ModelInfo(id="gpt-3.5-turbo",   provider="openai", name="GPT-3.5 Turbo",    context_length=16385,  pricing_input_per_1k=0.50,  pricing_output_per_1k=1.50,  capabilities=["chat", "streaming", "tools"]),
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
                    headers={"Authorization": f"Bearer {self.config.api_key}"},
                )
                return resp.status_code == 200
        except Exception:
            self.status = ProviderStatus.UNAVAILABLE
            return False

    async def list_models(self) -> list[ModelInfo]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.config.base_url}/models",
                    headers={"Authorization": f"Bearer {self.config.api_key}"},
                )
                resp.raise_for_status()
                data = resp.json()
                self.models = [
                    ModelInfo(
                        id=m["id"],
                        provider="openai",
                        name=m["id"],
                        context_length=128000,
                        pricing_input_per_1k=self.MODEL_MAP.get(m["id"], ModelInfo).pricing_input_per_1k if m["id"] in self.MODEL_MAP else 0.0,
                        pricing_output_per_1k=self.MODEL_MAP.get(m["id"], ModelInfo).pricing_output_per_1k if m["id"] in self.MODEL_MAP else 0.0,
                        capabilities=["chat", "streaming"],
                    )
                    for m in data.get("data", [])
                    if "gpt" in m["id"]
                ]
        except Exception:
            pass
        return self.models or list(self.MODEL_MAP.values())

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

        choice = data["choices"][0]
        content = choice["message"]["content"] or ""
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
            "stream_options": {"include_usage": True},
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
                        import json
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
                        except json.JSONDecodeError:
                            continue

        yield "", final_usage
