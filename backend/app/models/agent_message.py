from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import enum


class DbMessageType(str, enum.Enum):
    TEXT = "text"
    COMMAND = "command"
    RESULT = "result"
    ERROR = "error"
    BROADCAST = "broadcast"
    REQUEST = "request"
    RESPONSE = "response"


class DbSenderType(str, enum.Enum):
    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"
    ORCHESTRATOR = "orchestrator"


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    sender_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sender_type: Mapped[DbSenderType] = mapped_column(SAEnum(DbSenderType), nullable=False)
    recipient_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    recipient_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[DbMessageType] = mapped_column(SAEnum(DbMessageType), default=DbMessageType.TEXT)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    channel: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("agents.id"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
