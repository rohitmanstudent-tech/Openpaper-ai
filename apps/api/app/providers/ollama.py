from collections.abc import AsyncIterator

import httpx

from app.config import get_settings
from app.providers.base import BaseProvider

settings = get_settings()


class OllamaProvider(BaseProvider):
    name = "ollama"
    default_model = settings.OLLAMA_DEFAULT_MODEL

    async def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={"model": model or self.default_model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")

    async def chat_stream(self, messages: list[dict], model: str | None = None, **kwargs) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=300) as client, client.stream(
            "POST",
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={"model": model or self.default_model, "messages": messages, "stream": True},
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    import json
                    try:
                        data = json.loads(line)
                        if content := data.get("message", {}).get("content"):
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []
