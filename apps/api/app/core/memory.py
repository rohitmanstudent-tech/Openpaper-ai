"""Memory Engine — agent memory with semantic recall, consolidation, and expiration.

Provides multi-tier memory (short-term, long-term, shared team, agent personal)
backed by Qdrant vector search.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.vector import (
    DEFAULT_COLLECTION_NAME,
    delete_point,
    get_point,
    upsert_point,
)
from app.core.vector import (
    scroll as vector_scroll,
)
from app.core.vector import (
    search as vector_search,
)
from app.models.memory import MemoryType, now_ts

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

SHORT_TERM_TTL = 86400  # 24 hours
CONSOLIDATION_IMPORTANCE_MIN = 0.6
CONSOLIDATION_AGE_SECONDS = 3600  # 1 hour
DEFAULT_RECALL_LIMIT = 10

IMPORTANCE_KEYWORDS = {
    "decision": 0.3,
    "approved": 0.3,
    "budget": 0.4,
    "deadline": 0.3,
    "contract": 0.4,
    "agreement": 0.3,
    "commitment": 0.3,
    "revenue": 0.4,
    "pricing": 0.3,
    "strategic": 0.3,
    "priority": 0.3,
    "urgent": 0.3,
    "critical": 0.4,
    "blocker": 0.3,
    "opportunity": 0.3,
    "partnership": 0.3,
    "investment": 0.4,
    "milestone": 0.3,
    "launch": 0.3,
    "customer": 0.2,
    "complaint": 0.3,
    "requirement": 0.2,
    "specification": 0.2,
    "compliance": 0.3,
    "regulation": 0.3,
}


# ── Singleton ───────────────────────────────────────────────────────────────

_memory_engine: "MemoryEngine | None" = None


def get_memory_engine() -> "MemoryEngine":
    global _memory_engine
    if _memory_engine is None:
        _memory_engine = MemoryEngine()
    return _memory_engine


def set_memory_engine(engine: "MemoryEngine | None") -> None:
    global _memory_engine
    _memory_engine = engine


# ── Memory Engine ──────────────────────────────────────────────────────────


class MemoryEngine:
    """Core memory engine with CRUD, semantic recall, consolidation, and expiration."""

    async def create(
        self,
        agent_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        user_id: str = "",
        namespace: str = "default",
        metadata: dict | None = None,
        ttl_seconds: int | None = None,
        importance_score: float | None = None,
    ) -> dict[str, Any]:
        ts = now_ts()
        point_id = str(uuid.uuid4())
        score = importance_score if importance_score is not None else self._score_importance(content)
        expires_at = None
        if memory_type == MemoryType.SHORT_TERM:
            ttl = ttl_seconds or SHORT_TERM_TTL
            expires_at = ts + ttl
        payload = {
            "agent_id": agent_id,
            "user_id": user_id,
            "namespace": namespace,
            "memory_type": memory_type.value,
            "content": content,
            "summary": self._summarize(content),
            "importance_score": score,
            "metadata": metadata or {},
            "created_at": ts,
            "expires_at": expires_at,
            "last_accessed_at": ts,
            "access_count": 0,
            "consolidated": False,
        }
        await upsert_point(
            collection=DEFAULT_COLLECTION_NAME,
            point_id=point_id,
            text=content,
            payload=payload,
        )
        logger.debug("Memory %s created: type=%s agent=%s", point_id[:8], memory_type.value, agent_id)
        return {"id": point_id, **payload}

    async def get(self, point_id: str) -> dict[str, Any] | None:
        point = await get_point(DEFAULT_COLLECTION_NAME, point_id)
        if point is None:
            return None
        payload = point["payload"]
        if self._is_expired(payload):
            await delete_point(DEFAULT_COLLECTION_NAME, point_id)
            return None
        await self._touch(point_id, payload)
        return _format_response(point)

    async def update(
        self,
        point_id: str,
        content: str | None = None,
        metadata: dict | None = None,
        importance_score: float | None = None,
        memory_type: MemoryType | None = None,
    ) -> dict[str, Any] | None:
        point = await get_point(DEFAULT_COLLECTION_NAME, point_id)
        if point is None:
            return None
        payload = dict(point["payload"])
        if content is not None:
            payload["content"] = content
            payload["summary"] = self._summarize(content)
        if metadata is not None:
            payload["metadata"] = {**payload.get("metadata", {}), **metadata}
        if importance_score is not None:
            payload["importance_score"] = importance_score
        if memory_type is not None:
            payload["memory_type"] = memory_type.value
        await upsert_point(
            collection=DEFAULT_COLLECTION_NAME,
            point_id=point_id,
            text=payload["content"],
            payload=payload,
        )
        return {"id": point_id, **payload}

    async def delete(self, point_id: str) -> bool:
        return await delete_point(DEFAULT_COLLECTION_NAME, point_id)

    async def recall(
        self,
        query: str,
        agent_id: str | None = None,
        user_id: str | None = None,
        namespace: str | None = None,
        memory_type: MemoryType | None = None,
        limit: int = DEFAULT_RECALL_LIMIT,
        min_score: float = 0.0,
        include_expired: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agent_id:
            filters["agent_id"] = agent_id
        if user_id:
            filters["user_id"] = user_id
        if namespace:
            filters["namespace"] = namespace
        if memory_type:
            filters["memory_type"] = memory_type.value
        if not include_expired:
            filters["expires_at"] = {"$gt": now_ts()}

        results = await vector_search(
            collection=DEFAULT_COLLECTION_NAME,
            query_text=query,
            filters=filters or None,
            limit=limit,
        )
        filtered = [r for r in results if r["score"] >= min_score]
        for r in filtered:
            await self._touch(r["id"], r["payload"])
        return [_format_response(r) for r in filtered]

    async def recall_agent_context(
        self,
        agent_id: str,
        query: str,
        limit: int = 5,
    ) -> str:
        memories = await self.recall(
            query=query,
            agent_id=agent_id,
            limit=limit,
            min_score=0.3,
        )
        if not memories:
            return ""
        lines = []
        for m in memories:
            lines.append(f"- [{m['memory_type']}] (importance: {m['importance_score']:.2f}) {m['content']}")
        return "Relevant past memories:\n" + "\n".join(lines)

    async def search(
        self,
        query_text: str,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        qfilters = dict(filters or {})
        qfilters.setdefault("expires_at", {"$gt": now_ts()})
        results = await vector_search(
            collection=DEFAULT_COLLECTION_NAME,
            query_text=query_text,
            filters=qfilters,
            limit=limit,
        )
        return [_format_response(r) for r in results if r["score"] >= min_score]

    async def consolidate(
        self,
        agent_id: str | None = None,
        namespace: str | None = None,
        min_importance: float = CONSOLIDATION_IMPORTANCE_MIN,
        max_count: int = 50,
    ) -> int:
        filters: dict[str, Any] = {
            "memory_type": MemoryType.SHORT_TERM.value,
            "consolidated": False,
            "importance_score": {"$gte": min_importance},
        }
        if agent_id:
            filters["agent_id"] = agent_id
        if namespace:
            filters["namespace"] = namespace
        results, _ = await vector_scroll(
            collection=DEFAULT_COLLECTION_NAME,
            filters=filters,
            limit=max_count,
        )
        count = 0
        for r in results:
            payload = r["payload"]
            created = payload.get("created_at", 0)
            age = now_ts() - created
            if age < CONSOLIDATION_AGE_SECONDS:
                continue
            payload["memory_type"] = MemoryType.LONG_TERM.value
            payload["consolidated"] = True
            payload["expires_at"] = None
            await upsert_point(
                collection=DEFAULT_COLLECTION_NAME,
                point_id=r["id"],
                text=payload["content"],
                payload=payload,
            )
            count += 1
        if count:
            logger.info("Consolidated %d memories (%s)", count, agent_id or "all")
        return count

    async def expire(self) -> int:
        now = now_ts()
        results, _ = await vector_scroll(
            collection=DEFAULT_COLLECTION_NAME,
            filters={"expires_at": {"$lt": now}},
            limit=100,
        )
        count = 0
        for r in results:
            await delete_point(DEFAULT_COLLECTION_NAME, r["id"])
            count += 1
        if count:
            logger.info("Expired %d memories", count)
        return count

    async def count(
        self,
        agent_id: str | None = None,
        memory_type: MemoryType | None = None,
    ) -> int:
        filters: dict[str, Any] = {}
        if agent_id:
            filters["agent_id"] = agent_id
        if memory_type:
            filters["memory_type"] = memory_type.value
        results, _ = await vector_scroll(
            collection=DEFAULT_COLLECTION_NAME,
            filters=filters or None,
            limit=10000,
        )
        return len(results)

    # ── Internal helpers ─────────────────────────────────────────────────

    def _score_importance(self, content: str) -> float:
        text = content.lower()
        score = 0.3
        word_count = len(text.split())
        if word_count > 100:
            score += 0.1
        if word_count > 300:
            score += 0.1
        for keyword, boost in IMPORTANCE_KEYWORDS.items():
            if keyword in text:
                score += boost
        return min(round(score, 2), 1.0)

    def _summarize(self, content: str, max_words: int = 20) -> str:
        words = content.split()
        if len(words) <= max_words:
            return content
        return " ".join(words[:max_words]) + "..."

    def _is_expired(self, payload: dict) -> bool:
        expires = payload.get("expires_at")
        if expires is None:
            return False
        return now_ts() > expires

    async def _touch(self, point_id: str, payload: dict) -> None:
        ts = now_ts()
        payload = dict(payload)
        payload["last_accessed_at"] = ts
        payload["access_count"] = payload.get("access_count", 0) + 1
        await upsert_point(
            collection=DEFAULT_COLLECTION_NAME,
            point_id=point_id,
            text=payload.get("content", ""),
            payload=payload,
        )


def _format_response(r: dict[str, Any]) -> dict[str, Any]:
    p = r.get("payload", {})
    return {
        "id": r["id"],
        "agent_id": p.get("agent_id", ""),
        "user_id": p.get("user_id", ""),
        "namespace": p.get("namespace", "default"),
        "memory_type": p.get("memory_type", "short_term"),
        "content": p.get("content", ""),
        "summary": p.get("summary", ""),
        "importance_score": p.get("importance_score", 0.5),
        "metadata": p.get("metadata", {}),
        "created_at": _fmt_ts(p.get("created_at")),
        "expires_at": _fmt_ts(p.get("expires_at")),
        "last_accessed_at": _fmt_ts(p.get("last_accessed_at")),
        "access_count": p.get("access_count", 0),
        "consolidated": p.get("consolidated", False),
        "score": r.get("score", 0.0),
    }


def _fmt_ts(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=UTC).isoformat()
