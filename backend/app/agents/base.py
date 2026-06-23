from abc import ABC
from typing import AsyncGenerator
from app.providers.registry import ProviderManager


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""
    system_prompt: str = ""

    def __init__(
        self,
        provider_manager: ProviderManager,
        model: str = "llama3.1",
        provider: str | None = None,
        temperature: float = 0.7,
    ):
        self.provider_manager = provider_manager
        self.model = model
        self.provider = provider
        self.temperature = temperature

    def _build_messages(self, user_input: str, context: list[dict] | None = None) -> list[dict]:
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": user_input})
        return messages

    async def process(self, user_input: str, context: list[dict] | None = None) -> str:
        messages = self._build_messages(user_input, context)
        content, _, _, _ = await self.provider_manager.chat(
            messages=messages,
            model=self.model,
            provider=self.provider,
            temperature=self.temperature,
        )
        return content

    async def process_stream(
        self, user_input: str, context: list[dict] | None = None
    ) -> AsyncGenerator[str, None]:
        messages = self._build_messages(user_input, context)
        async for event in self.provider_manager.chat_stream(
            messages=messages,
            model=self.model,
            provider=self.provider,
            temperature=self.temperature,
        ):
            if event["type"] == "chunk":
                yield event["content"]
