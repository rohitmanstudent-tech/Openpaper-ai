from abc import ABC
from collections.abc import AsyncIterator

from app.core.memory import get_memory_engine
from app.providers import get_provider


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""
    system_prompt: str = ""
    agent_id: str = ""

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "llama3.1",
        temperature: float = 0.7,
        agent_id: str = "",
    ):
        self.provider_name = provider
        self.model = model
        self.temperature = temperature
        self.agent_id = agent_id

    def _build_messages(self, user_input: str, context: list[dict] | None = None) -> list[dict]:
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": user_input})
        return messages

    async def process(self, user_input: str, context: list[dict] | None = None) -> str:
        provider = get_provider(self.provider_name)
        if not provider:
            raise RuntimeError(f"Provider '{self.provider_name}' not available")
        messages = self._build_messages(user_input, context)
        result = await provider.chat(messages, model=self.model)
        await self._store_memory(user_input, result)
        return result

    async def process_stream(self, user_input: str, context: list[dict] | None = None) -> AsyncIterator[str]:
        provider = get_provider(self.provider_name)
        if not provider:
            raise RuntimeError(f"Provider '{self.provider_name}' not available")
        messages = self._build_messages(user_input, context)
        full = ""
        async for chunk in provider.chat_stream(messages, model=self.model):
            full += chunk
            yield chunk
        if full:
            await self._store_memory(user_input, full)

    async def remember(
        self,
        content: str,
        memory_type: str = "agent_personal",
        namespace: str = "default",
    ) -> dict | None:
        engine = get_memory_engine()
        return await engine.create(
            agent_id=self.agent_id or self.name,
            content=content,
            memory_type=memory_type,
            namespace=namespace,
        )

    async def recall(self, query: str, limit: int = 5) -> list[dict]:
        engine = get_memory_engine()
        return await engine.recall(
            query=query,
            agent_id=self.agent_id or self.name,
            limit=limit,
            min_score=0.3,
        )

    async def recall_context(self, query: str, limit: int = 5) -> str:
        engine = get_memory_engine()
        return await engine.recall_agent_context(
            agent_id=self.agent_id or self.name,
            query=query,
            limit=limit,
        )

    async def _store_memory(self, user_input: str, response: str) -> None:
        try:
            engine = get_memory_engine()
            interaction = f"User: {user_input}\nResponse: {response}"
            await engine.create(
                agent_id=self.agent_id or self.name,
                content=interaction[:2000],
                memory_type="short_term",
                namespace="default",
            )
        except Exception:
            pass
