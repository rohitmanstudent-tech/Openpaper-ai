"""Memory Engine API routes."""

from typing import Any

from fastapi import APIRouter, Depends

from app.core.exceptions import NotFoundError
from app.core.memory import get_memory_engine
from app.core.security import get_current_user
from app.models import User
from app.models.memory import (
    ConsolidationRequest,
    MemoryCreate,
    MemorySearch,
    MemoryUpdate,
)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


@router.post("/points")
async def create_memory(body: MemoryCreate, current_user: User = Depends(get_current_user)):
    engine = get_memory_engine()
    result = await engine.create(
        agent_id=body.agent_id,
        content=body.content,
        memory_type=body.memory_type,
        user_id=body.user_id or str(current_user.id),
        namespace=body.namespace,
        metadata=body.metadata,
        ttl_seconds=body.ttl_seconds,
    )
    return {"success": True, "memory": result}


@router.get("/points/{point_id}")
async def get_memory(point_id: str, current_user: User = Depends(get_current_user)):
    engine = get_memory_engine()
    result = await engine.get(point_id)
    if not result:
        raise NotFoundError(f"Memory {point_id} not found")
    return {"success": True, "memory": result}


@router.put("/points/{point_id}")
async def update_memory(point_id: str, body: MemoryUpdate, current_user: User = Depends(get_current_user)):
    engine = get_memory_engine()
    result = await engine.update(
        point_id=point_id,
        content=body.content,
        metadata=body.metadata,
        importance_score=body.importance_score,
        memory_type=body.memory_type,
    )
    if not result:
        raise NotFoundError(f"Memory {point_id} not found")
    return {"success": True, "memory": result}


@router.delete("/points/{point_id}")
async def delete_memory(point_id: str, current_user: User = Depends(get_current_user)):
    engine = get_memory_engine()
    await engine.delete(point_id)
    return {"success": True}


@router.post("/recall")
async def recall_memories(body: MemorySearch, current_user: User = Depends(get_current_user)):
    engine = get_memory_engine()
    results = await engine.recall(
        query=body.query,
        agent_id=body.agent_id,
        user_id=body.user_id,
        namespace=body.namespace,
        memory_type=body.memory_type,
        limit=body.limit,
        min_score=body.min_score,
        include_expired=body.include_expired,
    )
    agent_context = ""
    if body.agent_id:
        agent_context = await engine.recall_agent_context(body.agent_id, body.query)
    return {
        "success": True,
        "results": results,
        "total": len(results),
        "agent_context": agent_context,
    }


@router.post("/search")
async def search_memories(body: MemorySearch, current_user: User = Depends(get_current_user)):
    engine = get_memory_engine()
    filters: dict[str, Any] = {}
    if body.agent_id:
        filters["agent_id"] = body.agent_id
    if body.user_id:
        filters["user_id"] = body.user_id
    if body.namespace:
        filters["namespace"] = body.namespace
    if body.memory_type:
        filters["memory_type"] = body.memory_type.value
    results = await engine.search(
        query_text=body.query,
        filters=filters or None,
        limit=body.limit,
        min_score=body.min_score,
    )
    return {"success": True, "results": results, "total": len(results)}


@router.post("/consolidate")
async def consolidate_memories(body: ConsolidationRequest, current_user: User = Depends(get_current_user)):
    engine = get_memory_engine()
    count = await engine.consolidate(
        agent_id=body.agent_id,
        namespace=body.namespace,
        min_importance=body.min_importance,
        max_count=body.max_count,
    )
    return {"success": True, "consolidated": count}


@router.post("/expire")
async def expire_memories(current_user: User = Depends(get_current_user)):
    engine = get_memory_engine()
    count = await engine.expire()
    return {"success": True, "expired": count}


@router.get("/count")
async def count_memories(
    agent_id: str | None = None,
    memory_type: str | None = None,
    current_user: User = Depends(get_current_user),
):
    engine = get_memory_engine()
    from app.models.memory import MemoryType

    mt = MemoryType(memory_type) if memory_type else None
    count = await engine.count(agent_id=agent_id, memory_type=mt)
    return {"success": True, "count": count}
