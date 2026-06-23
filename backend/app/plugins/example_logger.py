import logging
from datetime import datetime, timezone

from app.plugins.base import BasePlugin, PluginHook

logger = logging.getLogger("plugins.logger")


class MessageLoggerPlugin(BasePlugin):
    name = "message_logger"
    version = "1.0.0"
    description = "Logs all agent bus messages and provider calls"

    @property
    def hooks(self) -> list[PluginHook]:
        return [
            PluginHook.ON_AGENT_MESSAGE,
            PluginHook.BEFORE_PROVIDER_CALL,
            PluginHook.AFTER_PROVIDER_CALL,
            PluginHook.STARTUP,
            PluginHook.SHUTDOWN,
        ]

    async def on_startup(self, app=None) -> None:
        logger.info("MessageLoggerPlugin started")

    async def on_shutdown(self, app=None) -> None:
        logger.info("MessageLoggerPlugin stopped")

    async def on_agent_message(self, message: dict) -> None:
        logger.info(
            "[MSG] %s -> %s | type=%s | len=%d",
            message.get("sender_id", "?"),
            message.get("recipient_id", "*") or "*",
            message.get("message_type", "?"),
            len(message.get("content", "") or ""),
        )

    async def before_provider_call(self, provider: str, model: str, messages: list[dict]) -> None:
        logger.info(
            "[PROVIDER] Calling %s/%s | messages=%d",
            provider, model, len(messages),
        )

    async def after_provider_call(self, provider: str, model: str, response: dict) -> None:
        logger.info(
            "[PROVIDER] %s/%s done | tokens=%s",
            provider, model,
            response.get("usage", {}).get("total_tokens", "?"),
        )
