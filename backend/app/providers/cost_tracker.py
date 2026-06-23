from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.provider_usage import ProviderUsage
from app.schemas.provider import UsageStatsResponse

# Pricing per 1M tokens (USD)
PRICING_TABLE: dict[str, dict[str, float]] = {
    # OpenAI
    "openai/gpt-4o":              {"input": 5.00,  "output": 15.00},
    "openai/gpt-4o-mini":         {"input": 0.15,  "output": 0.60},
    "openai/gpt-4-turbo":         {"input": 10.00, "output": 30.00},
    "openai/gpt-3.5-turbo":       {"input": 0.50,  "output": 1.50},
    # Anthropic
    "claude/claude-3-5-sonnet":   {"input": 3.00,  "output": 15.00},
    "claude/claude-3-haiku":      {"input": 0.25,  "output": 1.25},
    "claude/claude-3-opus":       {"input": 15.00, "output": 75.00},
    # Google
    "gemini/gemini-1.5-pro":      {"input": 3.50,  "output": 10.50},
    "gemini/gemini-1.5-flash":    {"input": 0.35,  "output": 1.05},
    # xAI
    "xai/grok-2":                 {"input": 2.00,  "output": 10.00},
    "xai/grok-2-mini":            {"input": 0.10,  "output": 0.50},
    # DeepSeek
    "deepseek/deepseek-chat":     {"input": 0.14,  "output": 0.28},
    "deepseek/deepseek-coder":    {"input": 0.14,  "output": 0.28},
    # OpenRouter (averages for popular)
    "openrouter/meta-llama-3.1":  {"input": 0.50,  "output": 0.50},
    # Ollama (free / local)
    "ollama/*":                   {"input": 0.0,   "output": 0.0},
    # NVIDIA NIM (free tier / self-hosted)
    "nvidia/*":                   {"input": 0.0,   "output": 0.0},
}


class CostTracker:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    def set_session(self, db: AsyncSession) -> None:
        self.db = db

    def get_pricing(self, provider: str, model: str) -> dict[str, float]:
        key = f"{provider}/{model}"
        if key in PRICING_TABLE:
            return PRICING_TABLE[key]
        wildcard = f"{provider}/*"
        if wildcard in PRICING_TABLE:
            return PRICING_TABLE[wildcard]
        return {"input": 0.0, "output": 0.0}

    def calculate_cost(
        self, provider: str, model: str, input_tokens: int, output_tokens: int
    ) -> dict[str, float]:
        pricing = self.get_pricing(provider, model)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(input_cost + output_cost, 6),
        }

    async def track(
        self,
        provider: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
        user_id: int | None = None,
        agent_id: int | None = None,
        chat_id: int | None = None,
        endpoint: str = "chat",
        status: str = "success",
        error_message: str | None = None,
    ) -> ProviderUsage | None:
        if not self.db:
            return None

        cost = self.calculate_cost(provider, model, input_tokens, output_tokens)

        usage = ProviderUsage(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens or (input_tokens + output_tokens),
            input_cost=cost["input_cost"],
            output_cost=cost["output_cost"],
            total_cost=cost["total_cost"],
            latency_ms=latency_ms,
            user_id=user_id,
            agent_id=agent_id,
            chat_id=chat_id,
            endpoint=endpoint,
            status=status,
            error_message=error_message,
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(usage)
        return usage

    async def get_usage(
        self,
        user_id: int | None = None,
        agent_id: int | None = None,
        provider: str | None = None,
        limit: int = 100,
    ) -> list[ProviderUsage]:
        if not self.db:
            return []
        query = select(ProviderUsage)
        if user_id:
            query = query.where(ProviderUsage.user_id == user_id)
        if agent_id:
            query = query.where(ProviderUsage.agent_id == agent_id)
        if provider:
            query = query.where(ProviderUsage.provider == provider)
        query = query.order_by(ProviderUsage.timestamp.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_aggregated(self, user_id: int | None = None) -> UsageStatsResponse:
        if not self.db:
            return UsageStatsResponse()

        query = select(
            func.sum(ProviderUsage.total_tokens).label("total_tokens"),
            func.sum(ProviderUsage.total_cost).label("total_cost"),
            func.count(ProviderUsage.id).label("total_requests"),
            func.avg(ProviderUsage.latency_ms).label("avg_latency_ms"),
        )
        if user_id:
            query = query.where(ProviderUsage.user_id == user_id)

        result = await self.db.execute(query)
        row = result.one()

        by_provider_query = select(
            ProviderUsage.provider,
            func.sum(ProviderUsage.total_tokens).label("tokens"),
            func.sum(ProviderUsage.total_cost).label("cost"),
            func.count(ProviderUsage.id).label("requests"),
        )
        if user_id:
            by_provider_query = by_provider_query.where(ProviderUsage.user_id == user_id)
        by_provider_query = by_provider_query.group_by(ProviderUsage.provider)
        by_provider_result = await self.db.execute(by_provider_query)
        by_provider = [
            {
                "provider": r[0],
                "total_tokens": int(r[1] or 0),
                "total_cost": round(float(r[2] or 0), 6),
                "total_requests": int(r[3] or 0),
            }
            for r in by_provider_result.all()
        ]

        return UsageStatsResponse(
            total_tokens=int(row.total_tokens or 0),
            total_cost=round(float(row.total_cost or 0), 6),
            total_requests=int(row.total_requests or 0),
            avg_latency_ms=round(float(row.avg_latency_ms or 0), 1),
            by_provider=by_provider,
        )
