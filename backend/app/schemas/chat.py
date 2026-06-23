from datetime import datetime
from pydantic import BaseModel


class ChatCreate(BaseModel):
    agent_id: int
    title: str | None = None


class ChatResponse(BaseModel):
    id: int
    title: str | None
    user_id: int
    agent_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    metadata: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageSend(BaseModel):
    content: str
    stream: bool = True
    provider: str | None = None
    model: str | None = None


class ChatWithMessages(ChatResponse):
    messages: list[MessageResponse] = []
