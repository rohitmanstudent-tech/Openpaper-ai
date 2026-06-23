from datetime import datetime

from pydantic import BaseModel


class ChatCreate(BaseModel):
    agent_id: int
    title: str | None = None


class MessageSend(BaseModel):
    content: str
    stream: bool = False


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    id: int
    title: str | None
    agent_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatWithMessages(ChatResponse):
    messages: list[MessageResponse] = []
