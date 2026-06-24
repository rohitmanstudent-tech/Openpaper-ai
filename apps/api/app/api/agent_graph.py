"""Agent Graph API — real-time agent network visualization, event streaming,
delegation chains, memory links, and health indicators backed by Event Bus data."""

import asyncio
import json
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import get_bus
from app.core.memory import get_memory_engine
from app.core.security import get_current_user
from app.core.vector import DEFAULT_COLLECTION_NAME
from app.core.vector import scroll as vector_scroll
from app.database import get_db
from app.models import User
from app.models.agent import Agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-graph", tags=["agent-graph"])


@router.get("/agents")
async def get_graph_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Agent).where(Agent.owner_id == current_user.id))
    agents = result.scalars().all()
    return {
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "agent_type": a.agent_type,
                "status": a.status,
                "model": a.model,
                "provider": a.provider,
                "is_active": a.is_active,
            }
            for a in agents
        ]
    }


@router.get("")
async def get_graph_state(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bus = get_bus()
    events = await bus.get_history(limit=100)
    result = await db.execute(select(Agent).where(Agent.owner_id == current_user.id))
    agents = result.scalars().all()

    agent_nodes = [
        {"id": f"agent_{a.id}", "type": "agent", "label": a.name, "agent_type": a.agent_type, "status": a.status}
        for a in agents
    ]

    delegations = [e for e in events if e.get("event_type") in ("agent_delegated", "message_sent")]
    memory_count = 0
    try:
        mem_results, _ = await vector_scroll(collection=DEFAULT_COLLECTION_NAME, filters={"type": "memory"}, limit=1)
        memory_count = len(mem_results)
    except Exception:
        pass

    edges = []
    for d in delegations:
        src = d.get("source_agent", "")
        tgt = d.get("target_agent", "")
        if src and tgt:
            edges.append(
                {
                    "source": f"agent_{src}",
                    "target": f"agent_{tgt}",
                    "event_type": d.get("event_type"),
                    "correlation_id": d.get("correlation_id"),
                }
            )

    return {
        "nodes": agent_nodes,
        "edges": edges,
        "events": events[:50],
        "memory_count": memory_count,
    }


@router.get("/events")
async def get_graph_events(
    limit: int = Query(50, ge=1, le=500),
    event_type: str | None = None,
):
    bus = get_bus()
    events = await bus.get_history(event_type=event_type, limit=limit)
    return {"events": events}


@router.get("/events/stream")
async def stream_graph_events(request: Request):
    """SSE endpoint for live agent events."""
    bus = get_bus()

    async def event_generator():
        last_count = 0
        while True:
            try:
                if await request.is_disconnected():
                    break
                events = await bus.get_history(limit=20)
                new_events = events[:10] if len(events) > last_count else []
                if new_events:
                    last_count = len(events)
                    yield f"data: {json.dumps({'events': new_events, 'timestamp': datetime.now(UTC).isoformat()})}\n\n"
                else:
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/delegations")
async def get_delegations(
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bus = get_bus()
    events = await bus.get_history(limit=limit)
    delegations = [e for e in events if e.get("event_type") in ("agent_delegated", "message_sent", "task_assigned")]
    return {"delegations": delegations}


@router.get("/memory-links")
async def get_memory_links(
    current_user: User = Depends(get_current_user),
):
    engine = get_memory_engine()
    try:
        count = await engine.count()
        results, _ = await vector_scroll(collection=DEFAULT_COLLECTION_NAME, limit=100)
        memories = []
        for r in results:
            p = r.get("payload", {})
            memories.append(
                {
                    "id": r["id"],
                    "agent_id": p.get("agent_id"),
                    "memory_type": p.get("memory_type"),
                    "content": p.get("content", "")[:100],
                    "importance_score": p.get("importance_score", 0.5),
                }
            )
    except Exception:
        count = 0
        memories = []

    return {
        "total": count,
        "memories": memories,
    }
