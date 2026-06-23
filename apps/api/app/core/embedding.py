"""Provider-agnostic embedding interface for vector generation.

Supports multiple backends: Ollama (local-first), OpenAI, or custom.
"""

import abc
import logging

logger = logging.getLogger(__name__)


class EmbeddingProvider(abc.ABC):
    """Abstract embedding provider."""

    @abc.abstractmethod
    async def embed(self, text: str) -> list[float]:
        ...

    @abc.abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...

    @property
    @abc.abstractmethod
    def dimension(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Uses Ollama's built-in /api/embeddings endpoint.

    Local-first, no API key required. Uses the same model as chat
    (e.g., llama3.1, nomic-embed-text, mxbai-embed-large).
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.base_url = base_url.rstrip("/")
        self._model = model
        self._dim = 768  # nomic-embed-text default; mxbai-embed-large=1024

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def name(self) -> str:
        return f"ollama/{self._model}"

    async def embed(self, text: str) -> list[float]:
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self._model, "prompt": text},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("embedding", [])

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results = []
        for t in texts:
            results.append(await self.embed(t))
        return results


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Uses OpenAI's text-embedding-3-small or text-embedding-3-large."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self._model = model
        self.base_url = base_url.rstrip("/")
        self._dim = 512 if "3-small" in model else 256 if "3-large" in model else 1536

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def name(self) -> str:
        return f"openai/{self._model}"

    async def embed(self, text: str) -> list[float]:
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self._model, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        import httpx
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self._model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
            data["data"].sort(key=lambda x: x["index"])
            return [item["embedding"] for item in data["data"]]


_embedding_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _embedding_provider
    if _embedding_provider is None:
        from app.config import get_settings
        s = get_settings()
        if s.OPENAI_API_KEY:
            _embedding_provider = OpenAIEmbeddingProvider(api_key=s.OPENAI_API_KEY)
            logger.info("Embedding: using OpenAI %s", _embedding_provider.name)
        else:
            _embedding_provider = OllamaEmbeddingProvider(base_url=s.OLLAMA_BASE_URL)
            logger.info("Embedding: using Ollama %s", _embedding_provider.name)
    return _embedding_provider


def set_embedding_provider(provider: EmbeddingProvider) -> None:
    global _embedding_provider
    _embedding_provider = provider
