"""Agent Communication Bus API routes."""

import uuid

from fastapi import APIRouter, Depends, Query

from app.core.event_bus import build_agent_message, get_bus, is_valid_direction
from app.core.exceptions import ValidationError
from app.core.security import get_current_user
from app.models import User
from app.models.events import (
    AgentMessage,
    AgentMessageDirection,
    EventType,
    TaskEvent,
    now_iso,
)

router = APIRouter(prefix="/api/v1/bus", tags=["bus"])


@router.get("/health")
async def bus_health():
    bus = get_bus()
    return await bus.health()


@router.post("/messages")
async def send_message(
    from_agent: str = Query(...),
    to_agent: str = Query(...),
    subject: str = Query(""),
    body: str = Query(...),
    correlation_id: str = Query(""),
    current_user: User = Depends(get_current_user),
):
    if not is_valid_direction(from_agent, to_agent):
        raise ValidationError(
            f"Invalid message direction: {from_agent} -> {to_agent}. "
            f"Allowed: ceo->research, research->buyer_finder, buyer_finder->sales, sales->ceo"
        )
    bus = get_bus()
    msg = AgentMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        subject=subject,
        body=body,
        correlation_id=correlation_id or "",
        created_at=now_iso(),
    )
    event_id = await bus.send_message(msg)
    return {"success": True, "event_id": event_id, "message": msg}


@router.get("/messages")
async def get_messages(
    event_type: str | None = Query(None),
    source_agent: str | None = Query(None),
    target_agent: str | None = Query(None),
    correlation_id: str | None = Query(None),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
):
    bus = get_bus()
    events = await bus.get_history(
        event_type=event_type,
        source_agent=source_agent,
        target_agent=target_agent,
        correlation_id=correlation_id,
        limit=limit,
    )
    return {"success": True, "events": events, "total": len(events)}


@router.post("/tasks")
async def create_task(
    title: str = Query(...),
    description: str = Query(""),
    assigned_agent: str = Query(""),
    priority: str = Query("medium"),
    correlation_id: str = Query(""),
    current_user: User = Depends(get_current_user),
):
    bus = get_bus()
    event = TaskEvent(
        title=title,
        description=description,
        assigned_agent=assigned_agent,
        status="pending",
        priority=priority,
        correlation_id=correlation_id or "",
        created_by=str(current_user.id),
        event_type=EventType.TASK_CREATED,
        created_at=now_iso(),
    )
    event_id = await bus.send_task_event(event)
    return {"success": True, "event_id": event_id, "task": event}


@router.post("/tasks/{task_id}/assign")
async def assign_task(
    task_id: str,
    assigned_agent: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    bus = get_bus()
    event = TaskEvent(
        task_id=task_id,
        assigned_agent=assigned_agent,
        status="in_progress",
        event_type=EventType.TASK_ASSIGNED,
        created_at=now_iso(),
    )
    event_id = await bus.send_task_event(event)
    return {"success": True, "event_id": event_id}


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    result: str = Query(""),
    current_user: User = Depends(get_current_user),
):
    bus = get_bus()
    event = TaskEvent(
        task_id=task_id,
        status="completed",
        result=result,
        event_type=EventType.TASK_COMPLETED,
        created_at=now_iso(),
    )
    event_id = await bus.send_task_event(event)
    return {"success": True, "event_id": event_id}


@router.post("/tasks/{task_id}/fail")
async def fail_task(
    task_id: str,
    error: str = Query(""),
    current_user: User = Depends(get_current_user),
):
    bus = get_bus()
    event = TaskEvent(
        task_id=task_id,
        status="failed",
        error=error,
        event_type=EventType.TASK_FAILED,
        created_at=now_iso(),
    )
    event_id = await bus.send_task_event(event)
    return {"success": True, "event_id": event_id}


@router.post("/tasks/{task_id}/delegate")
async def delegate_task(
    task_id: str,
    from_agent: str = Query(...),
    to_agent: str = Query(...),
    instruction: str = Query(""),
    current_user: User = Depends(get_current_user),
):
    if not is_valid_direction(from_agent, to_agent):
        raise ValidationError(f"Invalid delegation direction: {from_agent} -> {to_agent}")
    bus = get_bus()
    correlation_id = str(uuid.uuid4())
    delegation_msg = build_agent_message(
        direction=AgentMessageDirection(f"{from_agent}_to_{to_agent}"),
        subject=f"Delegation: {task_id}",
        body=instruction,
        correlation_id=correlation_id,
        metadata={"task_id": task_id},
    )
    await bus.send_message(delegation_msg)
    task_event = TaskEvent(
        task_id=task_id,
        assigned_agent=to_agent,
        status="in_progress",
        correlation_id=correlation_id,
        event_type=EventType.AGENT_DELEGATED,
        created_at=now_iso(),
    )
    event_id = await bus.send_task_event(task_event)
    return {
        "success": True,
        "event_id": event_id,
        "correlation_id": correlation_id,
        "from": from_agent,
        "to": to_agent,
    }


@router.post("/events/replay")
async def replay_events(
    event_type: str | None = Query(None),
    correlation_id: str | None = Query(None),
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_user),
):
    bus = get_bus()
    count = await bus.replay(
        event_type=event_type,
        correlation_id=correlation_id,
        limit=limit,
    )
    return {"success": True, "replayed": count}


@router.get("/events/types")
async def list_event_types():
    return {"success": True, "event_types": [e.value for e in EventType]}


@router.post("/publish")
async def publish_event(
    event_type: str = Query(...),
    source_agent: str = Query(""),
    target_agent: str = Query(""),
    data: str = Query("{}"),
    current_user: User = Depends(get_current_user),
):
    import json

    bus = get_bus()
    try:
        payload_data = json.loads(data)
    except json.JSONDecodeError:
        payload_data = {}
    event_id = await bus.publish(
        event_type=event_type,
        data=payload_data,
        source_agent=source_agent,
        target_agent=target_agent,
    )
    return {"success": True, "event_id": event_id}
