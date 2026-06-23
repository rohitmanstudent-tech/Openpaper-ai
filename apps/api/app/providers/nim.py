"""NVIDIA NIM provider — local-first, GPU-accelerated, OpenAI-compatible.

Supports local NVIDIA NIM containers (localhost:8000) with automatic GPU
detection, RTX optimization hints, and optional cloud API fallback.
"""

import json
import logging
import shutil
import subprocess
from collections.abc import AsyncIterator

import httpx

from app.config import get_settings
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

settings = get_settings()

LOCAL_NIM_BASE_URL = "http://localhost:8000"
CLOUD_NIM_BASE_URL = "https://api.nvcf.nvidia.com/v1"

COST_PER_1K_TOKENS = {
    "local": {"input": 0.0, "output": 0.0},
    "cloud": {"input": 0.00300, "output": 0.01500},
}

RTX_OPTIMIZED_MODELS = [
    "meta/llama-3.1-8b-instruct",
    "meta/llama-3.1-70b-instruct",
    "mistralai/mistral-7b-instruct-v0.3",
    "mistralai/mixtral-8x7b-instruct-v0.1",
    "nvidia/nemotron-4-340b-instruct",
]


def detect_gpu() -> dict:
    """Detect NVIDIA GPU and return capability info.

    Returns dict with:
      - available: bool
      - gpu_name: str (empty if not detected)
      - is_rtx: bool
      - cuda_version: str (empty if not detected)
      - vram_gb: float (0 if not detected)
    """
    result = {
        "available": False,
        "gpu_name": "",
        "is_rtx": False,
        "cuda_version": "",
        "vram_gb": 0.0,
    }
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return result
    try:
        output = subprocess.check_output(
            [
                nvidia_smi,
                "--query-gpu=name,memory.total,compute_cap",
                "--format=csv,noheader,nounits",
            ],
            timeout=5,
            text=True,
        )
        lines = output.strip().splitlines()
        if not lines:
            return result
        parts = [p.strip() for p in lines[0].split(",")]
        gpu_name = parts[0] if len(parts) > 0 else ""
        vram_mib = float(parts[1]) if len(parts) > 1 else 0.0
        result["available"] = True
        result["gpu_name"] = gpu_name
        result["vram_gb"] = round(vram_mib / 1024, 1)
        result["is_rtx"] = "RTX" in gpu_name.upper()
        if len(parts) > 2:
            result["cuda_version"] = parts[2]
        logger.info("Detected GPU: %s (RTX=%s, VRAM=%.1f GB)", gpu_name, result["is_rtx"], result["vram_gb"])
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    return result


class NimProvider(BaseProvider):
    name = "nim"
    default_model = "meta/llama-3.1-8b-instruct"
    api_key = getattr(settings, "NVIDIA_API_KEY", "")
    base_url = getattr(settings, "NIM_BASE_URL", LOCAL_NIM_BASE_URL)
    _gpu_info: dict | None = None
    _using_cloud: bool = False

    def __init__(self, api_key: str = "", base_url: str = ""):
        super().__init__()
        if api_key:
            self.api_key = api_key
        if base_url:
            self.base_url = base_url
        self._usage: list[dict] = []
        self._detect_and_configure()

    @property
    def gpu_info(self) -> dict:
        if self._gpu_info is None:
            self._gpu_info = detect_gpu()
        return self._gpu_info

    @property
    def using_cloud(self) -> bool:
        return self._using_cloud

    def _detect_and_configure(self) -> None:
        gpu = self.gpu_info
        if gpu["available"] and gpu["is_rtx"]:
            logger.info("RTX GPU detected — NIM optimized for local inference")
        if not gpu["available"] and self.api_key:
            self._using_cloud = True
            self.base_url = CLOUD_NIM_BASE_URL

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._using_cloud and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _url(self) -> str:
        return f"{self.base_url}/chat/completions"

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
                raise RuntimeError("NVIDIA NIM API key is invalid")
            if resp.status_code == 402:
                raise RuntimeError("NVIDIA NIM account has insufficient balance")
            if resp.status_code == 429:
                raise RuntimeError("NVIDIA NIM rate limit exceeded")
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError("NVIDIA NIM returned no choices")
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
        async with httpx.AsyncClient(timeout=300) as client, client.stream(
            "POST", self._url(),
            headers=self._headers(), json=body,
        ) as resp:
            if resp.status_code == 401:
                raise RuntimeError("NVIDIA NIM API key is invalid")
            if resp.status_code == 402:
                raise RuntimeError("NVIDIA NIM account has insufficient balance")
            if resp.status_code == 429:
                raise RuntimeError("NVIDIA NIM rate limit exceeded")
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
            self._record_usage(model_name, {
                "prompt_tokens": total_input,
                "completion_tokens": total_output,
            })

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        if self._using_cloud:
            return await self._list_cloud_models()
        return self._list_local_models()

    async def _list_cloud_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [m["id"] for m in data.get("data", [])]
        except Exception:
            pass
        return ["nvidia/nemotron-4-340b-instruct"]

    def _list_local_models(self) -> list[str]:
        gpu = self.gpu_info
        if gpu["available"] and gpu["is_rtx"] and gpu["vram_gb"] >= 16:
            return RTX_OPTIMIZED_MODELS
        if gpu["available"] and gpu["vram_gb"] >= 8:
            return ["meta/llama-3.1-8b-instruct", "mistralai/mistral-7b-instruct-v0.3"]
        return ["meta/llama-3.1-8b-instruct"]

    @staticmethod
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        rates = COST_PER_1K_TOKENS["local"] if "local" in model or model == "" else COST_PER_1K_TOKENS["cloud"]
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
        self._usage.append({
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
        })
        logger.debug(
            "NIM usage: model=%s prompt=%d completion=%d total=%d cost=$%.6f",
            model, prompt_tokens, completion_tokens, total_tokens, cost,
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
