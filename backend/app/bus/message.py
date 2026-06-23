from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    TEXT = "text"
    COMMAND = "command"
    RESULT = "result"
    ERROR = "error"
    BROADCAST = "broadcast"
    REQUEST = "request"
    RESPONSE = "response"


class SenderType(str, Enum):
    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"
    ORCHESTRATOR = "orchestrator"


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{datetime.now(timezone.utc).timestamp()}")
    sender_id: str
    sender_type: SenderType = SenderType.AGENT
    recipient_id: str | None = None
    recipient_type: str | None = None
    content: str
    message_type: MessageType = MessageType.TEXT
    correlation_id: str | None = None
    thread_id: str | None = None
    channel: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_redis(self) -> dict:
        return self.model_dump(mode="json")

    @classmethod
    def from_redis(cls, data: dict) -> "AgentMessage":
        return cls.model_validate(data)
