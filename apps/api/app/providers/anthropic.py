import json
from collections.abc import AsyncIterator

import httpx

from app.config import get_settings
from app.providers.base import BaseProvider

settings = get_settings()


class AnthropicProvider(BaseProvider):
    name = "claude"
    default_model = settings.ANTHROPIC_DEFAULT_MODEL
    api_key = settings.ANTHROPIC_API_KEY
    base_url = settings.ANTHROPIC_BASE_URL

    async def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> str:
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                filtered.append(m)

        body = {
            "model": model or self.default_model,
            "messages": filtered,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def chat_stream(self, messages: list[dict], model: str | None = None, **kwargs) -> AsyncIterator[str]:
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                filtered.append(m)

        body = {
            "model": model or self.default_model,
            "messages": filtered,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": True,
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=300) as client, client.stream(
            "POST",
            f"{self.base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=body,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    try:
                        chunk = json.loads(line[6:])
                        if chunk["type"] == "content_block_delta":
                            yield chunk["delta"]["text"]
                    except (json.JSONDecodeError, KeyError):
                        continue

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/models",
                    headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        return ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
