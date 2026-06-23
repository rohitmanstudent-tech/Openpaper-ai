from datetime import datetime
from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    agent_type: str
    description: str | None = None
    model: str = "llama3.1"
    provider: str = "ollama"
    system_prompt: str | None = None
    temperature: float = 0.7


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    model: str | None = None
    provider: str | None = None
    system_prompt: str | None = None
    temperature: float | None = None
    status: str | None = None
    is_active: bool | None = None


class AgentResponse(BaseModel):
    id: int
    name: str
    agent_type: str
    description: str | None
    status: str
    model: str
    provider: str
    system_prompt: str | None
    temperature: float
    is_active: bool
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
