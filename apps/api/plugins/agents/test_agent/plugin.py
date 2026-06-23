"""Test agent plugin for unit testing."""

from app.core.plugin_base import AgentPlugin


class TestAgentPlugin(AgentPlugin):
    name = "test_agent"
    version = "2.0.0"
    description = "A test agent plugin"

    async def process(self, user_input: str, context: list | None = None) -> str:
        return f"test agent processed: {user_input}"

    async def process_stream(self, user_input: str, context: list | None = None):
        yield f"test agent stream: {user_input}"
