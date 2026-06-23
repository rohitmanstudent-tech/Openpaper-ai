import json
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.api.deps import get_db, get_agent_bus, get_plugin_manager
from app.bus.bus import AgentBus
from app.bus.message import AgentMessage, MessageType, SenderType
from app.models.agent_message import AgentMessage as AgentMessageModel, DbSenderType, DbMessageType
from app.plugins.registry import PluginManager

router = APIRouter()


@router.post("/publish")
async def publish_message(
    message: AgentMessage,
    bus: AgentBus = Depends(get_agent_bus),
    db: AsyncSession = Depends(get_db),
):
    count = await bus.publish(message)

    db_msg = AgentMessageModel(
        id=message.id,
        sender_id=message.sender_id,
        sender_type=DbSenderType(message.sender_type.value),
        recipient_id=message.recipient_id,
        recipient_type=message.recipient_type,
        content=message.content,
        message_type=DbMessageType(message.message_type.value),
        correlation_id=message.correlation_id,
        thread_id=message.thread_id,
        channel=message.channel,
        metadata_json=json.dumps(message.metadata) if message.metadata else None,
    )
    db.add(db_msg)
    await db.commit()

    return {"status": "published", "message_id": message.id, "channels": count}


@router.get("/messages")
async def list_messages(
    thread_id: str | None = Query(None),
    sender_id: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(AgentMessageModel).order_by(desc(AgentMessageModel.created_at))
    if thread_id:
        query = query.where(AgentMessageModel.thread_id == thread_id)
    if sender_id:
        query = query.where(AgentMessageModel.sender_id == sender_id)
    query = query.limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_type": m.sender_type.value,
            "recipient_id": m.recipient_id,
            "content": m.content,
            "message_type": m.message_type.value,
            "correlation_id": m.correlation_id,
            "thread_id": m.thread_id,
            "metadata": json.loads(m.metadata_json) if m.metadata_json else {},
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.post("/request")
async def send_request(
    message: AgentMessage,
    timeout: int = Query(30, le=120),
    bus: AgentBus = Depends(get_agent_bus),
):
    message.message_type = MessageType.REQUEST
    response = await bus.request(message, timeout=timeout)
    if response is None:
        raise HTTPException(status_code=504, detail="No response received within timeout")
    return response


@router.websocket("/ws")
async def bus_websocket(
    websocket: WebSocket,
    agent_id: str | None = Query(None),
    agent_type: str | None = Query(None),
):
    await websocket.accept()

    from app.main import get_agent_bus as _get_bus
    bus = _get_bus()
    if bus is None:
        await websocket.send_json({"error": "Agent bus not initialized"})
        await websocket.close()
        return

    try:
        async for message in bus.subscribe(agent_id=agent_id, agent_type=agent_type):
            await websocket.send_json(message.to_redis())
    except WebSocketDisconnect:
        pass
