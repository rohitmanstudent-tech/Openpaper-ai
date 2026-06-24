"""Google Gemini provider — plugin-based, compatible with ProviderRegistry.

Supports Gemini 2.5 Pro and Gemini 2.5 Flash with streaming,
chat completions, model listing, token tracking, and cost analytics.
"""

import json
import logging
from collections.abc import AsyncIterator

import httpx

from app.config import get_settings
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

settings = get_settings()

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

COST_PER_1K_TOKENS = {
    "gemini-2.5-pro": {"input": 0.00125, "output": 0.00500},
    "gemini-2.5-flash": {"input": 0.00015, "output": 0.00060},
}


def _count_tokens(text: str) -> int:
    return len(text.split())


class GeminiProvider(BaseProvider):
    name = "gemini"
    default_model = "gemini-2.5-flash"
    api_key = settings.GEMINI_API_KEY
    base_url = GEMINI_BASE_URL

    def __init__(self, api_key: str = "", base_url: str = ""):
        if api_key:
            self.api_key = api_key
        if base_url:
            self.base_url = base_url
        self._usage: list[dict] = []

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

    def _url(self, model: str, stream: bool = False) -> str:
        endpoint = "streamGenerateContent" if stream else "generateContent"
        return f"{self.base_url}/models/{model}:{endpoint}"

    def _format_messages(self, messages: list[dict]) -> list[dict]:
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                contents.append(
                    {
                        "role": "user",
                        "parts": [{"text": f"[System instruction]: {msg['content']}"}],
                    }
                )
            elif role == "assistant":
                contents.append(
                    {
                        "role": "model",
                        "parts": [{"text": msg["content"]}],
                    }
                )
            else:
                contents.append(
                    {
                        "role": "user",
                        "parts": [{"text": msg["content"]}],
                    }
                )
        return contents

    async def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> str:
        model_name = model or self.default_model
        body = {
            "contents": self._format_messages(messages),
            "generationConfig": self._build_config(**kwargs),
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(self._url(model_name), headers=self._headers(), json=body)
            if resp.status_code == 403:
                raise RuntimeError("Gemini API key is invalid or missing")
            if resp.status_code == 429:
                raise RuntimeError("Gemini rate limit exceeded")
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini returned no candidates")
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            usage = data.get("usageMetadata", {})
            self._record_usage(model_name, usage)
            return text

    async def chat_stream(self, messages: list[dict], model: str | None = None, **kwargs) -> AsyncIterator[str]:
        model_name = model or self.default_model
        body = {
            "contents": self._format_messages(messages),
            "generationConfig": self._build_config(**kwargs),
        }
        total_input = 0
        total_output = 0
        async with (
            httpx.AsyncClient(timeout=300) as client,
            client.stream(
                "POST",
                self._url(model_name, stream=True),
                headers=self._headers(),
                json=body,
            ) as resp,
        ):
            if resp.status_code == 403:
                raise RuntimeError("Gemini API key is invalid or missing")
            if resp.status_code == 429:
                raise RuntimeError("Gemini rate limit exceeded")
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                if line.startswith("data: "):
                    line = line[6:]
                try:
                    chunk = json.loads(line)
                    parts = chunk.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    for part in parts:
                        if text := part.get("text", ""):
                            yield text
                    usage = chunk.get("usageMetadata", {})
                    if usage:
                        total_input = usage.get("promptTokenCount", total_input)
                        total_output = usage.get("candidatesTokenCount", total_output)
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue
        if total_input or total_output:
            self._record_usage(
                model_name,
                {
                    "promptTokenCount": total_input,
                    "candidatesTokenCount": total_output,
                },
            )

    async def check_health(self) -> bool:
        try:
            model_name = self.default_model
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/models/{model_name}?key={self.api_key}",
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/models?key={self.api_key}",
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        m["name"].replace("models/", "")
                        for m in data.get("models", [])
                        if "gemini" in m.get("name", "")
                    ]
        except Exception:
            pass
        return ["gemini-2.5-pro", "gemini-2.5-flash"]

    @staticmethod
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        rates = COST_PER_1K_TOKENS.get(model, COST_PER_1K_TOKENS["gemini-2.5-flash"])
        return (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])

    def _build_config(self, **kwargs) -> dict:
        config = {}
        if "temperature" in kwargs:
            config["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs or "maxOutputTokens" in kwargs:
            config["maxOutputTokens"] = kwargs.get("maxOutputTokens", kwargs.get("max_tokens", 8192))
        if "top_p" in kwargs:
            config["topP"] = kwargs["top_p"]
        if "top_k" in kwargs:
            config["topK"] = kwargs["top_k"]
        if "stop" in kwargs:
            config["stopSequences"] = kwargs["stop"] if isinstance(kwargs["stop"], list) else [kwargs["stop"]]
        return config

    def _record_usage(self, model: str, usage: dict) -> None:
        prompt_tokens = usage.get("promptTokenCount", 0)
        candidates_tokens = usage.get("candidatesTokenCount", 0)
        total_tokens = usage.get("totalTokenCount", prompt_tokens + candidates_tokens)
        cost = self.estimate_cost(model, prompt_tokens, candidates_tokens)
        self._usage.append(
            {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": candidates_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
            }
        )
        logger.debug(
            "Gemini usage: model=%s prompt=%d candidates=%d total=%d cost=$%.6f",
            model,
            prompt_tokens,
            candidates_tokens,
            total_tokens,
            cost,
        )

    def get_usage(self) -> list[dict]:
        return list(self._usage)

    def get_total_usage(self) -> dict:
        prompt = sum(u["prompt_tokens"] for u in self._usage)
        completion = sum(u["completion_tokens"] for u in self._usage)
        total = sum(u["total_tokens"] for u in self._usage)
        cost = sum(u["cost"] for u in self._usage)
        return {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": total,
            "cost": round(cost, 6),
        }
