import json
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

from redis.asyncio import Redis

from app.bus.message import AgentMessage, MessageType, SenderType
from app.plugins.registry import PluginManager


class AgentBus:
    def __init__(self, redis: Redis, plugin_manager: PluginManager | None = None):
        self.redis = redis
        self.plugin_manager = plugin_manager
        self._pubsub = None

    async def publish(self, message: AgentMessage) -> int:
        if self.plugin_manager:
            modified = await self.plugin_manager.on_agent_message(message.to_redis())
            if modified is not None:
                message = AgentMessage.from_redis(modified)

        data = json.dumps(message.to_redis())

        channels = [f"agent:messages"]
        if message.recipient_id:
            channels.append(f"agent:{message.recipient_id}")
        if message.sender_type == SenderType.AGENT:
            channels.append(f"agent:type:{message.sender_id}")

        count = 0
        for ch in channels:
            count += await self.redis.publish(ch, data)

        message_key = f"bus:messages:{message.id}"
        await self.redis.setex(message_key, 86400, data)

        return count

    async def subscribe(
        self,
        agent_id: str | None = None,
        agent_type: str | None = None,
    ) -> AsyncGenerator[AgentMessage, None]:
        self._pubsub = self.redis.pubsub()

        channels = ["agent:messages"]
        if agent_id:
            channels.append(f"agent:{agent_id}")
        if agent_type:
            channels.append(f"agent:type:{agent_type}")

        await self._pubsub.subscribe(*channels)

        try:
            async for raw in self._pubsub.listen():
                if raw["type"] != "message":
                    continue
                try:
                    data = json.loads(raw["data"])
                    yield AgentMessage.from_redis(data)
                except (json.JSONDecodeError, KeyError):
                    continue
        finally:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()

    async def request(
        self,
        message: AgentMessage,
        timeout: float = 30.0,
    ) -> AgentMessage | None:
        if message.correlation_id is None:
            message.correlation_id = str(uuid.uuid4())
        if message.message_type != MessageType.REQUEST:
            message.message_type = MessageType.REQUEST

        response_queue = f"bus:responses:{message.correlation_id}"

        await self.publish(message)

        result = await self.redis.brpoplpush(
            response_queue,
            f"{response_queue}:processed",
            timeout=int(timeout),
        )

        if result is None:
            return None

        try:
            data = json.loads(result)
            return AgentMessage.from_redis(data)
        except (json.JSONDecodeError, KeyError):
            return None

    async def respond(self, original: AgentMessage, content: str, metadata: dict | None = None) -> int:
        response = AgentMessage(
            id=f"resp_{original.correlation_id}_{datetime.now(timezone.utc).timestamp()}",
            sender_id=original.recipient_id or "system",
            sender_type=SenderType.AGENT,
            recipient_id=original.sender_id,
            content=content,
            message_type=MessageType.RESPONSE,
            correlation_id=original.correlation_id,
            thread_id=original.thread_id,
            metadata=metadata or {},
        )

        if original.correlation_id:
            response_key = f"bus:responses:{original.correlation_id}"
            data = json.dumps(response.to_redis())
            await self.redis.lpush(response_key, data)
            await self.redis.expire(response_key, 300)

        return await self.publish(response)

    async def get_history(self, thread_id: str, limit: int = 50) -> list[AgentMessage]:
        pattern = f"bus:messages:*"
        messages = []
        cursor = 0
        while cursor is not None:
            cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=100)
            for key in keys:
                data = await self.redis.get(key)
                if data is None:
                    continue
                try:
                    msg = AgentMessage.from_redis(json.loads(data))
                    if msg.thread_id == thread_id:
                        messages.append(msg)
                except (json.JSONDecodeError, KeyError):
                    continue
            if cursor == 0:
                break

        messages.sort(key=lambda m: m.timestamp)
        return messages[-limit:]

    async def close(self) -> None:
        if self._pubsub:
            await self._pubsub.close()
