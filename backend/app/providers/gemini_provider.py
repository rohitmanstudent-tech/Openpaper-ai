import json
import httpx
from typing import AsyncGenerator

from app.providers.base import BaseProvider, ProviderConfig, ModelInfo, ProviderStatus


class GeminiProvider(BaseProvider):
    provider_name = "gemini"
    default_model = "gemini-1.5-pro"

    def __init__(self, config: ProviderConfig | None = None):
        super().__init__(config)
        self.models = [
            ModelInfo(id="gemini-1.5-pro",       provider="gemini", name="Gemini 1.5 Pro",       context_length=1048576, pricing_input_per_1k=3.50,  pricing_output_per_1k=10.50, capabilities=["chat", "streaming", "vision", "tools", "code"]),
            ModelInfo(id="gemini-1.5-flash",      provider="gemini", name="Gemini 1.5 Flash",     context_length=1048576, pricing_input_per_1k=0.35,  pricing_output_per_1k=1.05,  capabilities=["chat", "streaming", "vision", "tools", "code"]),
            ModelInfo(id="gemini-1.0-pro",        provider="gemini", name="Gemini 1.0 Pro",       context_length=32768,   pricing_input_per_1k=0.50,  pricing_output_per_1k=1.50,  capabilities=["chat", "streaming"]),
        ]

    async def is_available(self) -> bool:
        if not self.config.api_key:
            self.status = ProviderStatus.UNCONFIGURED
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                url = f"{self.config.base_url}/models?key={self.config.api_key}"
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            self.status = ProviderStatus.UNAVAILABLE
            return False

    async def list_models(self) -> list[ModelInfo]:
        return self.models

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        gemini_contents = []
        for m in messages:
            if m["role"] == "system":
                gemini_contents.append({"role": "user", "parts": [{"text": f"[System Instruction]: {m['content']}"}]})
                gemini_contents.append({"role": "model", "parts": [{"text": "Understood, I will follow these instructions."}]})
            elif m["role"] == "user":
                gemini_contents.append({"role": "user", "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                gemini_contents.append({"role": "model", "parts": [{"text": m["content"]}]})
        return gemini_contents

    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> tuple[str, dict]:
        contents = self._convert_messages(messages)
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            },
        }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        model_id = model or self.default_model
        url = f"{self.config.base_url}/models/{model_id}:generateContent?key={self.config.api_key}"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)

        usage_data = data.get("usageMetadata", {})
        usage = {
            "input_tokens": usage_data.get("promptTokenCount", 0),
            "output_tokens": usage_data.get("candidatesTokenCount", 0),
            "total_tokens": usage_data.get("totalTokenCount", 0),
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
        contents = self._convert_messages(messages)
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            },
        }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        model_id = model or self.default_model
        url = f"{self.config.base_url}/models/{model_id}:streamGenerateContent?alt=sse&key={self.config.api_key}"

        final_usage = {}
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    if "text" in p:
                                        yield p["text"], {}
                            if chunk.get("usageMetadata"):
                                u = chunk["usageMetadata"]
                                final_usage = {
                                    "input_tokens": u.get("promptTokenCount", 0),
                                    "output_tokens": u.get("candidatesTokenCount", 0),
                                    "total_tokens": u.get("totalTokenCount", 0),
                                }
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

        yield "", final_usage
