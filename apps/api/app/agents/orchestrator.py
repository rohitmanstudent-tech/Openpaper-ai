from collections.abc import AsyncIterator

from app.agents.base import BaseAgent
from app.agents.buyer_finder import BuyerFinderAgent
from app.agents.ceo import CEOAgent
from app.agents.research import ResearchAgent
from app.agents.sales import SalesAgent
from app.core.memory import get_memory_engine
from app.models.agent import AgentType


class AgentOrchestrator:
    def __init__(self, default_provider: str = "ollama", default_model: str = "llama3.1"):
        self.default_provider = default_provider
        self.default_model = default_model
        self._agents: dict[str, BaseAgent] = {}

    def _get_agent_class(self, agent_type: AgentType):
        mapping = {
            AgentType.CEO: CEOAgent,
            AgentType.SALES: SalesAgent,
            AgentType.RESEARCH: ResearchAgent,
            AgentType.BUYER_FINDER: BuyerFinderAgent,
        }
        cls = mapping.get(agent_type)
        if not cls:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return cls

    def get_agent(
        self,
        agent_type: AgentType,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        agent_id: str = "",
    ):
        key = f"{agent_type.value}:{provider or self.default_provider}:{model or self.default_model}:{agent_id}"
        if key not in self._agents:
            cls = self._get_agent_class(agent_type)
            self._agents[key] = cls(
                provider=provider or self.default_provider,
                model=model or self.default_model,
                temperature=temperature,
                agent_id=agent_id or agent_type.value,
            )
        return self._agents[key]

    async def _enrich_with_memory(
        self, agent_type: AgentType, user_input: str, context: list[dict] | None
    ) -> list[dict]:
        enriched = list(context) if context else []
        try:
            engine = get_memory_engine()
            memories = await engine.recall(
                query=user_input,
                agent_id=agent_type.value,
                limit=5,
                min_score=0.3,
            )
            if memories:
                memory_text = "Relevant past memories:\n" + "\n".join(
                    f"- [{m['memory_type']}] {m['content']}" for m in memories
                )
                enriched.append({"role": "system", "content": memory_text})
        except Exception:
            pass
        return enriched

    async def process(
        self,
        agent_type: AgentType,
        user_input: str,
        context: list[dict] | None = None,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        agent_id: str = "",
    ) -> str:
        agent = self.get_agent(agent_type, provider, model, temperature, agent_id)
        enriched = await self._enrich_with_memory(agent_type, user_input, context)
        return await agent.process(user_input, enriched)

    async def process_stream(
        self,
        agent_type: AgentType,
        user_input: str,
        context: list[dict] | None = None,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        agent_id: str = "",
    ) -> AsyncIterator[str]:
        agent = self.get_agent(agent_type, provider, model, temperature, agent_id)
        enriched = await self._enrich_with_memory(agent_type, user_input, context)
        async for chunk in agent.process_stream(user_input, enriched):
            yield chunk
