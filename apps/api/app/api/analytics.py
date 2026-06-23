"""Analytics API — enterprise dashboards for providers, costs, agents,
workflows, memory, documents, and system health."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import get_bus
from app.core.health import deep_check
from app.core.memory import get_memory_engine
from app.core.security import get_current_user
from app.core.vector import DEFAULT_COLLECTION_NAME
from app.core.vector import scroll as vector_scroll
from app.database import get_db
from app.models import User
from app.models.agent import Agent
from app.models.memory import MemoryType
from app.models.workflow import RunStatus, Workflow, WorkflowRun
from app.providers import get_providers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])

PROVIDER_NAMES = ["openai", "anthropic", "gemini", "deepseek", "grok", "openrouter", "ollama", "nim"]


@router.get("/providers")
async def get_provider_analytics():
    providers = get_providers()
    results = {}
    for name in PROVIDER_NAMES:
        prov = providers.get(name)
        if prov:
            try:
                healthy = await prov.check_health()
            except Exception:
                healthy = False
            results[name] = {
                "name": name,
                "status": "available" if healthy else "unavailable",
                "models_count": len(await prov.list_models()) if healthy else 0,
            }
        else:
            results[name] = {"name": name, "status": "not_configured", "models_count": 0}
    return {"providers": results}


@router.get("/costs")
async def get_cost_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {
        "daily": [],
        "weekly": [],
        "monthly": [],
        "per_provider": {n: 0 for n in PROVIDER_NAMES},
        "per_agent": {},
        "per_workflow": {},
        "total_estimated_cost": 0,
    }


@router.get("/agents")
async def get_agent_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Agent).where(Agent.owner_id == current_user.id))
    agents = result.scalars().all()
    bus = get_bus()
    events = await bus.get_history(limit=500)

    agent_stats = {}
    for a in agents:
        agent_events = [
            e for e in events
            if e.get("source_agent") == a.agent_type or e.get("target_agent") == a.agent_type
        ]
        delegations = len([e for e in agent_events if e.get("event_type") == "agent_delegated"])
        tasks_completed = len([e for e in agent_events if e.get("event_type") == "task_completed"])
        tasks_failed = len([e for e in agent_events if e.get("event_type") == "task_failed"])
        messages = len([e for e in agent_events if e.get("event_type") == "message_sent"])

        agent_stats[a.agent_type] = {
            "id": a.id,
            "name": a.name,
            "agent_type": a.agent_type,
            "status": a.status,
            "tasks_completed": tasks_completed,
            "tasks_failed": tasks_failed,
            "delegation_count": delegations,
            "message_count": messages,
            "total_events": len(agent_events),
        }

    return {
        "agents": agent_stats,
        "total_agents": len(agents),
        "active_agents": sum(1 for a in agents if a.status == "idle" or a.status == "working"),
        "most_active": max(agent_stats.values(), key=lambda x: x["total_events"]) if agent_stats else None,
    }


@router.get("/workflows")
async def get_workflow_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow).where(Workflow.owner_id == current_user.id).order_by(Workflow.updated_at.desc())
    )
    workflows = result.scalars().all()

    total_runs = 0
    successful_runs = 0
    failed_runs = 0
    total_duration = 0.0
    workflow_stats = []

    for wf in workflows:
        runs_result = await db.execute(
            select(WorkflowRun).where(WorkflowRun.workflow_id == wf.id)
        )
        runs = runs_result.scalars().all()
        wf_runs = len(runs)
        wf_success = sum(1 for r in runs if r.status == RunStatus.COMPLETED)
        wf_failed = sum(1 for r in runs if r.status == RunStatus.FAILED)
        wf_duration = 0.0
        for r in runs:
            if r.started_at and r.completed_at:
                wf_duration += (r.completed_at - r.started_at).total_seconds()

        total_runs += wf_runs
        successful_runs += wf_success
        failed_runs += wf_failed
        total_duration += wf_duration

        workflow_stats.append({
            "id": wf.id,
            "name": wf.name,
            "status": wf.status,
            "total_runs": wf_runs,
            "successful_runs": wf_success,
            "failed_runs": wf_failed,
            "avg_duration": round(wf_duration / wf_runs, 2) if wf_runs > 0 else 0,
        })

    return {
        "workflows": workflow_stats,
        "total_workflows": len(workflows),
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "avg_duration": round(total_duration / total_runs, 2) if total_runs > 0 else 0,
    }


@router.get("/memory")
async def get_memory_analytics():
    get_memory_engine()
    try:
        results, _ = await vector_scroll(collection=DEFAULT_COLLECTION_NAME, limit=1000)
        memories = []
        for r in results:
            p = r.get("payload", {})
            if p.get("type") == "memory":
                memories.append(p)

        total = len(memories)
        long_term = sum(1 for m in memories if m.get("memory_type") == MemoryType.LONG_TERM.value)
        short_term = sum(1 for m in memories if m.get("memory_type") == MemoryType.SHORT_TERM.value)
        shared = sum(1 for m in memories if m.get("memory_type") == MemoryType.SHARED_TEAM.value)
        agent_personal = sum(1 for m in memories if m.get("memory_type") == MemoryType.AGENT_PERSONAL.value)
    except Exception:
        total = long_term = short_term = shared = agent_personal = 0
        memories = []

    return {
        "total": total,
        "long_term": long_term,
        "short_term": short_term,
        "shared": shared,
        "agent_personal": agent_personal,
        "recent": memories[:20],
    }


@router.get("/documents")
async def get_document_analytics():
    try:
        results, _ = await vector_scroll(collection="documents", limit=1000)
        docs = [r.get("payload", {}) for r in results]
        total_docs = len(docs)
        total_chunks = sum(d.get("chunk_count", 0) for d in docs)
    except Exception:
        total_docs = 0
        total_chunks = 0
        docs = []

    try:
        search_results, _ = await vector_scroll(collection="knowledge_base", limit=1)
        searches = len(search_results)
    except Exception:
        searches = 0

    top_docs = sorted(docs, key=lambda d: d.get("chunk_count", 0), reverse=True)[:10]

    return {
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "searches_performed": searches,
        "top_documents": [
            {"id": d.get("document_id"), "title": d.get("title"), "chunk_count": d.get("chunk_count")}
            for d in top_docs
        ],
    }


@router.get("/system")
async def get_system_analytics():
    checks = await deep_check()

    bus = get_bus()
    bus_health = await bus.health()

    checks["checks"]["event_bus"] = bus_health
    checks["checks"]["api"] = {"status": "healthy", "version": checks.get("version", "unknown")}

    return {
        "status": checks.get("status", "unknown"),
        "uptime_seconds": checks.get("uptime_seconds", 0),
        "version": checks.get("version", ""),
        "checks": checks.get("checks", {}),
    }
