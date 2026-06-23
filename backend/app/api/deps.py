from typing import AsyncGenerator
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.providers.registry import ProviderManager
from app.plugins.registry import PluginManager
from app.bus.bus import AgentBus


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


def get_plugin_manager(request: Request) -> PluginManager:
    return request.app.state.plugin_manager


def get_agent_bus(request: Request) -> AgentBus | None:
    return request.app.state.agent_bus


def get_provider_manager(request: Request) -> ProviderManager:
    return request.app.state.provider_manager


async def get_ollama():
    from app.main import get_provider_manager as _get_pm
    pm = _get_pm()
    if pm is None:
        return None
    return pm.get_provider("ollama")
