"""Pydantic schemas for the Memory Engine."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MemoryType(StrEnum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SHARED_TEAM = "shared_team"
    AGENT_PERSONAL = "agent_personal"


class MemoryCreate(BaseModel):
    agent_id: str
    user_id: str = ""
    namespace: str = "default"
    memory_type: MemoryType = MemoryType.SHORT_TERM
    content: str
    metadata: dict = {}
    ttl_seconds: int | None = None


class MemoryUpdate(BaseModel):
    content: str | None = None
    metadata: dict | None = None
    importance_score: float | None = Field(None, ge=0.0, le=1.0)
    memory_type: MemoryType | None = None


class MemoryResponse(BaseModel):
    id: str
    agent_id: str
    user_id: str
    namespace: str
    memory_type: MemoryType
    content: str
    summary: str = ""
    importance_score: float = 0.5
    metadata: dict = {}
    created_at: str
    expires_at: str | None = None
    last_accessed_at: str
    access_count: int = 0
    consolidated: bool = False
    score: float = 0.0


class MemorySearch(BaseModel):
    query: str
    agent_id: str | None = None
    user_id: str | None = None
    namespace: str | None = None
    memory_type: MemoryType | None = None
    limit: int = 10
    min_score: float = 0.0
    include_expired: bool = False


class MemoryRecallResult(BaseModel):
    query: str
    results: list[MemoryResponse]
    total: int
    agent_context: str = ""


class ConsolidationRequest(BaseModel):
    agent_id: str | None = None
    namespace: str | None = None
    min_importance: float = 0.6
    max_count: int = 50


def now_ts() -> float:
    return datetime.now(UTC).timestamp()
