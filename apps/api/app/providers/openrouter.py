from collections.abc import AsyncIterator

import httpx

from app.config import get_settings
from app.providers.base import BaseProvider

settings = get_settings()


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    default_model = settings.OPENROUTER_DEFAULT_MODEL
    api_key = settings.OPENROUTER_API_KEY
    base_url = settings.OPENROUTER_BASE_URL

    async def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": model or self.default_model, "messages": messages, **kwargs},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict], model: str | None = None, **kwargs) -> AsyncIterator[str]:
        async with (
            httpx.AsyncClient(timeout=300) as client,
            client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": model or self.default_model, "messages": messages, "stream": True, **kwargs},
            ) as resp,
        ):
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line.strip() != "data: [DONE]":
                    import json

                    try:
                        chunk = json.loads(line[6:])
                        if delta := chunk["choices"][0].get("delta", {}).get("content"):
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    async def check_health(self) -> bool:
        return bool(self.api_key)

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [m["id"] for m in data.get("data", [])]
        except Exception:
            pass
        return []
