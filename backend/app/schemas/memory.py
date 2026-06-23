from datetime import datetime
from pydantic import BaseModel


class MemoryCreate(BaseModel):
    content: str
    memory_type: str = "long_term"
    scope: str = "private"
    agent_id: int | None = None
    source: str | None = None
    tags: str | None = None


class MemoryResponse(BaseModel):
    id: int
    content: str
    memory_type: str
    scope: str
    user_id: int | None
    agent_id: int | None
    source: str | None
    embedding_id: str | None
    tags: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemorySearch(BaseModel):
    query: str
    limit: int = 10
    scope: str | None = None
