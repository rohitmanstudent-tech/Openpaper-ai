from datetime import datetime
from pydantic import BaseModel


class ProviderStatusResponse(BaseModel):
    name: str
    status: str
    default_model: str
    model_count: int
    capabilities: list[str]
    local: bool


class ModelInfoResponse(BaseModel):
    id: str
    provider: str
    name: str
    context_length: int
    pricing_input_per_1k: float
    pricing_output_per_1k: float
    capabilities: list[str]
    available: bool


class CompareRequest(BaseModel):
    prompt: str
    models: list[str]
    temperature: float = 0.3
    max_tokens: int | None = 512


class CompareResponse(BaseModel):
    model: str
    provider: str | None = None
    content: str | None = None
    latency_ms: float | None = None
    usage: dict | None = None
    error: str | None = None


class UsageRecord(BaseModel):
    id: int
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    total_cost: float
    latency_ms: float
    user_id: int | None
    agent_id: int | None
    status: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class UsageByProvider(BaseModel):
    provider: str
    total_tokens: int
    total_cost: float
    total_requests: int


class UsageStatsResponse(BaseModel):
    total_tokens: int = 0
    total_cost: float = 0.0
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    by_provider: list[UsageByProvider] = []


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    provider: str | None = None
    messages: list[dict]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False


class ChatCompletionResponse(BaseModel):
    content: str
    provider: str
    model: str
    usage: dict | None = None
