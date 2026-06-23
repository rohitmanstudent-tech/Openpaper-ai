"""Structured event schemas for the Agent Communication Bus."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel


class EventType(StrEnum):
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    MEMORY_CREATED = "memory_created"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    MESSAGE_SENT = "message_sent"
    AGENT_DELEGATED = "agent_delegated"
    AGENT_RESPONDED = "agent_responded"


class AgentMessageDirection(StrEnum):
    CEO_TO_RESEARCH = "ceo_to_research"
    RESEARCH_TO_BUYER_FINDER = "research_to_buyer_finder"
    BUYER_FINDER_TO_SALES = "buyer_finder_to_sales"
    SALES_TO_CEO = "sales_to_ceo"


DIRECTION_MAP: dict[AgentMessageDirection, tuple[str, str]] = {
    AgentMessageDirection.CEO_TO_RESEARCH: ("ceo", "research"),
    AgentMessageDirection.RESEARCH_TO_BUYER_FINDER: ("research", "buyer_finder"),
    AgentMessageDirection.BUYER_FINDER_TO_SALES: ("buyer_finder", "sales"),
    AgentMessageDirection.SALES_TO_CEO: ("sales", "ceo"),
}


class EventPayload(BaseModel):
    event_id: str = ""
    event_type: EventType
    correlation_id: str = ""
    source_agent: str = ""
    target_agent: str = ""
    timestamp: str = ""
    data: dict = {}


class AgentMessage(BaseModel):
    message_id: str = ""
    direction: AgentMessageDirection | None = None
    from_agent: str
    to_agent: str
    subject: str = ""
    body: str = ""
    correlation_id: str = ""
    parent_message_id: str = ""
    event_type: EventType = EventType.MESSAGE_SENT
    metadata: dict = {}
    created_at: str = ""


class TaskEvent(BaseModel):
    task_id: str
    title: str = ""
    description: str = ""
    assigned_agent: str = ""
    assigned_to: str = ""
    status: str = "pending"
    priority: str = "medium"
    result: str = ""
    error: str = ""
    correlation_id: str = ""
    created_by: str = ""
    event_type: EventType = EventType.TASK_CREATED
    created_at: str = ""


class SubscriptionRequest(BaseModel):
    event_types: list[EventType] | None = None
    callback_url: str = ""
    agent_id: str = ""


class BusHealth(BaseModel):
    status: str = "available"
    mode: str = "memory"
    events_published: int = 0
    active_subscriptions: int = 0
    stored_events: int = 0


def now_iso() -> str:
    return datetime.now(UTC).isoformat()
