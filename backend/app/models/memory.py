from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import enum


class MemoryType(str, enum.Enum):
    LONG_TERM = "long_term"
    AGENT = "agent"
    TEAM = "team"


class MemoryScope(str, enum.Enum):
    PRIVATE = "private"
    AGENT = "agent"
    TEAM = "team"
    GLOBAL = "global"


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[MemoryType] = mapped_column(SAEnum(MemoryType), nullable=False)
    scope: Mapped[MemoryScope] = mapped_column(SAEnum(MemoryScope), default=MemoryScope.PRIVATE)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agents.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(255), nullable=True)
    embedding_id: Mapped[str] = mapped_column(String(255), nullable=True)
    tags: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
