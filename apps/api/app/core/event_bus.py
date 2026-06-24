"""Agent Communication Bus — async pub/sub event system with Redis + in-memory fallback.

Provides agent-to-agent messaging, task lifecycle events, workflow orchestration,
event persistence via Qdrant, and event replay capabilities.
"""

import logging
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from app.core.redis import redis_client
from app.core.vector import scroll as vector_scroll
from app.core.vector import upsert_point
from app.models.events import (
    DIRECTION_MAP,
    AgentMessage,
    AgentMessageDirection,
    EventPayload,
    EventType,
    TaskEvent,
    now_iso,
)

logger = logging.getLogger(__name__)

EVENTS_COLLECTION = "agent_events"
EventHandler = Callable[[EventPayload], Coroutine[Any, Any, None]]


class EventBus:
    """Async pub/sub event bus with Redis backend and in-memory fallback.

    Attributes:
        mode: 'redis' if Redis connected, else 'memory'
        handlers: dict of event_type -> list of async callables
    """

    def __init__(self):
        self.mode: str = "memory"
        self.handlers: dict[str, list[EventHandler]] = {}
        self._count: int = 0
        self._pubsub = None

    async def start(self) -> None:
        if redis_client is not None:
            try:
                await redis_client.ping()
                self.mode = "redis"
                self._pubsub = redis_client.pubsub()
                logger.info("EventBus: using Redis pub/sub")
            except Exception:
                self.mode = "memory"
                logger.info("EventBus: using in-memory (Redis unavailable)")
        else:
            self.mode = "memory"
            logger.info("EventBus: using in-memory")

    async def stop(self) -> None:
        if self._pubsub:
            await self._pubsub.close()

    async def publish(
        self,
        event_type: EventType | str,
        data: dict | AgentMessage | TaskEvent | None = None,
        source_agent: str = "",
        target_agent: str = "",
        correlation_id: str = "",
    ) -> str:
        event_id = str(uuid.uuid4())
        cid = correlation_id or str(uuid.uuid4())
        payload_dict = data.model_dump() if isinstance(data, (AgentMessage, TaskEvent)) else data or {}

        payload = EventPayload(
            event_id=event_id,
            event_type=EventType(event_type) if isinstance(event_type, str) else event_type,
            correlation_id=cid,
            source_agent=source_agent,
            target_agent=target_agent,
            timestamp=now_iso(),
            data=payload_dict,
        )
        self._count += 1

        # persist to Qdrant
        try:
            await self._persist_event(payload)
        except Exception as e:
            logger.debug("Event persistence skipped: %s", e)

        # publish
        if self.mode == "redis":
            try:
                channel = f"agentbus:{payload.event_type.value}"
                await redis_client.publish(channel, payload.model_dump_json())
            except Exception as e:
                logger.warning("Redis publish failed, falling back to in-memory: %s", e)
                await self._dispatch_local(payload)
        else:
            await self._dispatch_local(payload)

        logger.debug("Event %s: %s from=%s to=%s", event_id[:8], payload.event_type.value, source_agent, target_agent)
        return event_id

    async def subscribe(self, event_type: EventType | str, handler: EventHandler) -> None:
        et = event_type.value if isinstance(event_type, EventType) else event_type
        if et not in self.handlers:
            self.handlers[et] = []
        self.handlers[et].append(handler)
        if self.mode == "redis" and self._pubsub:
            try:
                channel = f"agentbus:{et}"
                await self._pubsub.subscribe(channel)
            except Exception:
                pass

    async def unsubscribe(self, event_type: EventType | str, handler: EventHandler) -> None:
        et = event_type.value if isinstance(event_type, EventType) else event_type
        if et in self.handlers:
            self.handlers[et] = [h for h in self.handlers[et] if h is not handler]

    async def get_history(
        self,
        event_type: EventType | str | None = None,
        source_agent: str | None = None,
        target_agent: str | None = None,
        correlation_id: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        filters: dict[str, Any] = {}
        if event_type:
            et = event_type.value if isinstance(event_type, EventType) else event_type
            filters["event_type"] = et
        if source_agent:
            filters["source_agent"] = source_agent
        if target_agent:
            filters["target_agent"] = target_agent
        if correlation_id:
            filters["correlation_id"] = correlation_id

        try:
            results, _ = await vector_scroll(
                collection=EVENTS_COLLECTION,
                filters=filters or None,
                limit=limit,
            )
            events = []
            for r in results:
                p = r.get("payload", {})
                ev = {
                    "event_id": p.get("event_id", r["id"]),
                    "event_type": p.get("event_type"),
                    "correlation_id": p.get("correlation_id"),
                    "source_agent": p.get("source_agent"),
                    "target_agent": p.get("target_agent"),
                    "timestamp": p.get("timestamp"),
                    "data": p.get("data", {}),
                }
                events.append(ev)
            events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
            return events[:limit]
        except Exception as e:
            logger.warning("Event history retrieval failed: %s", e)
            return []

    async def replay(
        self,
        event_type: EventType | str | None = None,
        correlation_id: str | None = None,
        limit: int = 100,
    ) -> int:
        events = await self.get_history(
            event_type=event_type,
            correlation_id=correlation_id,
            limit=limit,
        )
        count = 0
        for ev in events:
            try:
                payload = EventPayload(**ev)
                await self._dispatch_local(payload)
                count += 1
            except Exception as e:
                logger.warning("Replay skipped event %s: %s", ev.get("event_id", "?"), e)
        logger.info("Replayed %d events", count)
        return count

    async def send_message(self, msg: AgentMessage) -> str:
        cid = msg.correlation_id or str(uuid.uuid4())
        return await self.publish(
            event_type=EventType.MESSAGE_SENT,
            data=msg,
            source_agent=msg.from_agent,
            target_agent=msg.to_agent,
            correlation_id=cid,
        )

    async def send_task_event(self, event: TaskEvent) -> str:
        return await self.publish(
            event_type=event.event_type,
            data=event,
            source_agent=event.assigned_agent or "",
            target_agent=event.assigned_to,
            correlation_id=event.correlation_id,
        )

    async def health(self) -> dict:
        try:
            events_stored = 0
            results, _ = await vector_scroll(collection=EVENTS_COLLECTION, limit=1)
            events_stored = len(results)
        except Exception:
            events_stored = 0
        return {
            "status": "available",
            "mode": self.mode,
            "events_published": self._count,
            "active_subscriptions": sum(len(h) for h in self.handlers.values()),
            "stored_events": events_stored,
        }

    # ── Internal ─────────────────────────────────────────────────────────

    async def _dispatch_local(self, payload: EventPayload) -> None:
        et = payload.event_type.value if isinstance(payload.event_type, EventType) else payload.event_type
        handlers = self.handlers.get(et, [])
        for handler in handlers:
            try:
                await handler(payload)
            except Exception as e:
                logger.error("Handler error for %s: %s", et, e)

    async def _persist_event(self, payload: EventPayload) -> None:
        await upsert_point(
            collection=EVENTS_COLLECTION,
            point_id=payload.event_id,
            text=f"{payload.event_type.value} {payload.source_agent} -> {payload.target_agent}",
            payload=payload.model_dump(),
        )


# ── Singleton ───────────────────────────────────────────────────────────────

_bus: EventBus | None = None


def get_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


def set_bus(bus: EventBus | None) -> None:
    global _bus
    _bus = bus


# ── Agent Communication Protocol ────────────────────────────────────────────


def build_agent_message(
    direction: AgentMessageDirection,
    subject: str,
    body: str,
    correlation_id: str = "",
    parent_message_id: str = "",
    metadata: dict | None = None,
) -> AgentMessage:
    from_agent, to_agent = DIRECTION_MAP[direction]
    return AgentMessage(
        message_id=str(uuid.uuid4()),
        direction=direction,
        from_agent=from_agent,
        to_agent=to_agent,
        subject=subject,
        body=body,
        correlation_id=correlation_id or str(uuid.uuid4()),
        parent_message_id=parent_message_id,
        metadata=metadata or {},
        created_at=now_iso(),
    )


def is_valid_direction(from_agent: str, to_agent: str) -> bool:
    return any(from_agent == f and to_agent == t for direction, (f, t) in DIRECTION_MAP.items())
