from typing import AsyncGenerator
from app.providers.registry import ProviderManager
from app.agents.ceo import CEOAgent
from app.agents.sales import SalesAgent
from app.agents.research import ResearchAgent
from app.agents.buyer_finder import BuyerFinderAgent
from app.agents.operations import OperationsAgent
from app.models.agent import AgentType
from app.bus.bus import AgentBus
from app.bus.message import AgentMessage, SenderType, MessageType


class AgentOrchestrator:
    def __init__(self, provider_manager: ProviderManager, agent_bus: AgentBus | None = None):
        self.provider_manager = provider_manager
        self.agent_bus = agent_bus
        self._agents = {}

    def get_agent(self, agent_type: AgentType, model: str = "llama3.1", temperature: float = 0.7, provider: str | None = None):
        key = (agent_type, model, provider)
        if key not in self._agents:
            self._agents[key] = self._create_agent(agent_type, model, temperature, provider)
        return self._agents[key]

    def _create_agent(self, agent_type: AgentType, model: str, temperature: float, provider: str | None):
        agents_map = {
            AgentType.CEO: CEOAgent,
            AgentType.SALES: SalesAgent,
            AgentType.RESEARCH: ResearchAgent,
            AgentType.BUYER_FINDER: BuyerFinderAgent,
            AgentType.OPERATIONS: OperationsAgent,
        }
        agent_class = agents_map.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return agent_class(
            provider_manager=self.provider_manager,
            model=model,
            temperature=temperature,
            provider=provider,
        )

    async def _broadcast_message(
        self,
        agent_type: AgentType,
        user_input: str,
        agent_id: str | None = None,
        thread_id: str | None = None,
    ) -> None:
        if not self.agent_bus:
            return
        msg = AgentMessage(
            sender_id=agent_id or agent_type.value,
            sender_type=SenderType.ORCHESTRATOR,
            content=user_input,
            message_type=MessageType.TEXT,
            thread_id=thread_id,
            metadata={"agent_type": agent_type.value},
        )
        await self.agent_bus.publish(msg)

    async def process(
        self,
        agent_type: AgentType,
        user_input: str,
        context: list[dict] | None = None,
        model: str = "llama3.1",
        temperature: float = 0.7,
        provider: str | None = None,
        thread_id: str | None = None,
    ) -> str:
        await self._broadcast_message(agent_type, user_input, thread_id=thread_id)
        agent = self.get_agent(agent_type, model, temperature, provider)
        result = await agent.process(user_input, context)
        if self.agent_bus:
            resp = AgentMessage(
                sender_id=agent_type.value,
                sender_type=SenderType.AGENT,
                content=result,
                message_type=MessageType.RESULT,
                thread_id=thread_id,
            )
            await self.agent_bus.publish(resp)
        return result

    async def process_stream(
        self,
        agent_type: AgentType,
        user_input: str,
        context: list[dict] | None = None,
        model: str = "llama3.1",
        temperature: float = 0.7,
        provider: str | None = None,
        thread_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        await self._broadcast_message(agent_type, user_input, thread_id=thread_id)
        agent = self.get_agent(agent_type, model, temperature, provider)
        full_content = ""
        async for chunk in agent.process_stream(user_input, context):
            full_content += chunk
            yield chunk
        if self.agent_bus:
            resp = AgentMessage(
                sender_id=agent_type.value,
                sender_type=SenderType.AGENT,
                content=full_content,
                message_type=MessageType.RESULT,
                thread_id=thread_id,
            )
            await self.agent_bus.publish(resp)
