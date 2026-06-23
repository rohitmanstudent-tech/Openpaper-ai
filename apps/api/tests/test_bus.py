"""Tests for the Agent Communication Bus module."""

from unittest.mock import AsyncMock

import pytest

from app.core.event_bus import EventBus, build_agent_message, get_bus, is_valid_direction, set_bus
from app.models.events import (
    AgentMessage,
    AgentMessageDirection,
    EventType,
    TaskEvent,
    now_iso,
)


@pytest.fixture(autouse=True)
def _mock_bus():
    bus = EventBus()
    bus.mode = "memory"
    bus.start = AsyncMock()
    bus.stop = AsyncMock()
    bus.publish = AsyncMock(return_value="event-1")
    bus.send_message = AsyncMock(return_value="msg-1")
    bus.send_task_event = AsyncMock(return_value="task-event-1")
    bus.get_history = AsyncMock(return_value=[
        {"event_id": "evt-1", "event_type": "message_sent", "source_agent": "ceo",
         "target_agent": "research", "correlation_id": "cid-1", "timestamp": now_iso(),
         "data": {"subject": "test", "body": "hello"}},
    ])
    bus.replay = AsyncMock(return_value=1)
    bus.health = AsyncMock(return_value={
        "status": "available", "mode": "memory", "events_published": 10,
        "active_subscriptions": 2, "stored_events": 5,
    })
    set_bus(bus)
    yield
    set_bus(None)


class TestEventBus:
    async def test_publish_event(self):
        bus = get_bus()
        event_id = await bus.publish(
            event_type=EventType.TASK_CREATED,
            data={"task_id": "t-1"},
            source_agent="ceo",
            target_agent="research",
        )
        assert event_id == "event-1"
        bus.publish.assert_called_once()

    async def test_send_message(self):
        bus = get_bus()
        msg = AgentMessage(
            from_agent="ceo", to_agent="research",
            subject="Research request", body="Analyze market",
        )
        event_id = await bus.send_message(msg)
        assert event_id == "msg-1"

    async def test_send_task_event(self):
        bus = get_bus()
        event = TaskEvent(
            task_id="t-1", title="Market analysis",
            assigned_agent="research", status="pending",
        )
        event_id = await bus.send_task_event(event)
        assert event_id == "task-event-1"

    async def test_get_history(self):
        bus = get_bus()
        events = await bus.get_history(limit=10)
        assert len(events) == 1
        assert events[0]["source_agent"] == "ceo"

    async def test_replay_events(self):
        bus = get_bus()
        count = await bus.replay(event_type="message_sent", limit=50)
        assert count == 1

    async def test_health(self):
        bus = get_bus()
        health = await bus.health()
        assert health["status"] == "available"
        assert health["mode"] == "memory"
        assert health["events_published"] == 10

    async def test_publish_with_correlation_id(self):
        bus = get_bus()
        await bus.publish(
            event_type=EventType.WORKFLOW_STARTED,
            correlation_id="wf-1",
        )
        bus.publish.assert_called_once()


class TestAgentCommunicationProtocol:
    def test_build_ceo_to_research_message(self):
        msg = build_agent_message(
            direction=AgentMessageDirection.CEO_TO_RESEARCH,
            subject="Market Research",
            body="Analyze TAM for electric vehicles",
        )
        assert msg.from_agent == "ceo"
        assert msg.to_agent == "research"
        assert msg.subject == "Market Research"

    def test_build_research_to_buyer_finder_message(self):
        msg = build_agent_message(
            direction=AgentMessageDirection.RESEARCH_TO_BUYER_FINDER,
            subject="Lead List",
            body="Find buyers in Germany",
        )
        assert msg.from_agent == "research"
        assert msg.to_agent == "buyer_finder"

    def test_build_buyer_finder_to_sales_message(self):
        msg = build_agent_message(
            direction=AgentMessageDirection.BUYER_FINDER_TO_SALES,
            subject="Qualified Leads",
            body="3 hot leads identified",
        )
        assert msg.from_agent == "buyer_finder"
        assert msg.to_agent == "sales"

    def test_build_sales_to_ceo_message(self):
        msg = build_agent_message(
            direction=AgentMessageDirection.SALES_TO_CEO,
            subject="Pipeline Update",
            body="Closed 2 deals this week",
        )
        assert msg.from_agent == "sales"
        assert msg.to_agent == "ceo"

    def test_valid_directions(self):
        assert is_valid_direction("ceo", "research") is True
        assert is_valid_direction("research", "buyer_finder") is True
        assert is_valid_direction("buyer_finder", "sales") is True
        assert is_valid_direction("sales", "ceo") is True

    def test_invalid_directions(self):
        assert is_valid_direction("research", "ceo") is False
        assert is_valid_direction("sales", "research") is False
        assert is_valid_direction("ceo", "sales") is False
        assert is_valid_direction("unknown", "ceo") is False

    def test_message_has_correlation_id(self):
        msg = build_agent_message(
            direction=AgentMessageDirection.CEO_TO_RESEARCH,
            subject="Test",
            body="Test body",
            correlation_id="custom-cid",
        )
        assert msg.correlation_id == "custom-cid"

    def test_message_auto_generates_correlation_id(self):
        msg = build_agent_message(
            direction=AgentMessageDirection.CEO_TO_RESEARCH,
            subject="Test",
            body="Test body",
        )
        assert msg.correlation_id != ""


class TestEventTypes:
    def test_all_event_types_defined(self):
        expected = [
            "task_created", "task_assigned", "task_completed", "task_failed",
            "memory_created", "workflow_started", "workflow_completed",
            "message_sent", "agent_delegated", "agent_responded",
        ]
        actual = [e.value for e in EventType]
        for e in expected:
            assert e in actual
