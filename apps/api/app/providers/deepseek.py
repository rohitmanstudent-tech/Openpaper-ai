"""DeepSeek provider — OpenAI-compatible, plugin-ready.

Supports DeepSeek Chat and DeepSeek Reasoner with streaming,
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

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

COST_PER_1K_TOKENS = {
    "deepseek-chat": {"input": 0.00027, "output": 0.00110},
    "deepseek-reasoner": {"input": 0.00055, "output": 0.00219},
}


class DeepSeekProvider(BaseProvider):
    name = "deepseek"
    default_model = "deepseek-chat"
    api_key = settings.DEEPSEEK_API_KEY
    base_url = getattr(settings, "DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL)

    def __init__(self, api_key: str = "", base_url: str = ""):
        if api_key:
            self.api_key = api_key
        if base_url:
            self.base_url = base_url
        self._usage: list[dict] = []

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _url(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    async def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> str:
        model_name = model or self.default_model
        body = {
            "model": model_name,
            "messages": messages,
            **self._build_config(**kwargs),
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(self._url(), headers=self._headers(), json=body)
            if resp.status_code == 401:
                raise RuntimeError("DeepSeek API key is invalid")
            if resp.status_code == 402:
                raise RuntimeError("DeepSeek account has insufficient balance")
            if resp.status_code == 429:
                raise RuntimeError("DeepSeek rate limit exceeded")
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError("DeepSeek returned no choices")
            text = choices[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            self._record_usage(model_name, usage)
            return text

    async def chat_stream(self, messages: list[dict], model: str | None = None, **kwargs) -> AsyncIterator[str]:
        model_name = model or self.default_model
        body = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            **self._build_config(**kwargs),
        }
        total_input = 0
        total_output = 0
        async with (
            httpx.AsyncClient(timeout=300) as client,
            client.stream(
                "POST",
                self._url(),
                headers=self._headers(),
                json=body,
            ) as resp,
        ):
            if resp.status_code == 401:
                raise RuntimeError("DeepSeek API key is invalid")
            if resp.status_code == 402:
                raise RuntimeError("DeepSeek account has insufficient balance")
            if resp.status_code == 429:
                raise RuntimeError("DeepSeek rate limit exceeded")
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                if line.startswith("data: "):
                    line = line[6:]
                if line.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(line)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    if text := delta.get("content", ""):
                        yield text
                    usage = chunk.get("usage", {})
                    if usage:
                        total_input = usage.get("prompt_tokens", total_input)
                        total_output = usage.get("completion_tokens", total_output)
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue
        if total_input or total_output:
            self._record_usage(
                model_name,
                {
                    "prompt_tokens": total_input,
                    "completion_tokens": total_output,
                },
            )

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/v1/models",
                    headers=self._headers(),
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/v1/models",
                    headers=self._headers(),
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [m["id"] for m in data.get("data", []) if "deepseek" in m.get("id", "")]
        except Exception:
            pass
        return ["deepseek-chat", "deepseek-reasoner"]

    @staticmethod
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        rates = COST_PER_1K_TOKENS.get(model, COST_PER_1K_TOKENS["deepseek-chat"])
        return (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])

    def _build_config(self, **kwargs) -> dict:
        config = {}
        if "temperature" in kwargs:
            config["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            config["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            config["top_p"] = kwargs["top_p"]
        if "stop" in kwargs:
            config["stop"] = kwargs["stop"] if isinstance(kwargs["stop"], list) else [kwargs["stop"]]
        if "frequency_penalty" in kwargs:
            config["frequency_penalty"] = kwargs["frequency_penalty"]
        if "presence_penalty" in kwargs:
            config["presence_penalty"] = kwargs["presence_penalty"]
        return config

    def _record_usage(self, model: str, usage: dict) -> None:
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        cost = self.estimate_cost(model, prompt_tokens, completion_tokens)
        self._usage.append(
            {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
            }
        )
        logger.debug(
            "DeepSeek usage: model=%s prompt=%d completion=%d total=%d cost=$%.6f",
            model,
            prompt_tokens,
            completion_tokens,
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
