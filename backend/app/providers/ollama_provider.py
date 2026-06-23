import json
import httpx
from typing import AsyncGenerator

from app.providers.base import BaseProvider, ProviderConfig, ModelInfo, ProviderStatus


class OllamaProvider(BaseProvider):
    provider_name = "ollama"
    default_model = "llama3.1"

    def __init__(self, config: ProviderConfig | None = None):
        super().__init__(config)
        if not self.config.base_url:
            from app.config import get_settings
            self.config.base_url = get_settings().OLLAMA_BASE_URL
        self.default_model = getattr(self.config, "default_model", "llama3.1") or "llama3.1"

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.config.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            self.status = ProviderStatus.UNAVAILABLE
            return False

    async def list_models(self) -> list[ModelInfo]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{self.config.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
            self.models = [
                ModelInfo(
                    id=m["name"],
                    provider="ollama",
                    name=m["name"],
                    context_length=8192,
                    pricing_input_per_1k=0.0,
                    pricing_output_per_1k=0.0,
                    capabilities=["chat", "streaming", "code"],
                )
                for m in data.get("models", [])
            ]
        except Exception:
            self.models = []
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
            "stream": False,
            "options": {"temperature": temperature},
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.config.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data.get("message", {}).get("content", "")
        usage = {
            "input_tokens": data.get("prompt_eval_count", 0),
            "output_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
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
            "stream": True,
            "options": {"temperature": temperature},
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self.config.base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                total_input = 0
                total_output = 0
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                yield chunk["message"]["content"], {}
                            if chunk.get("done"):
                                total_input = chunk.get("prompt_eval_count", 0)
                                total_output = chunk.get("eval_count", 0)
                        except json.JSONDecodeError:
                            continue

        yield "", {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
        }
