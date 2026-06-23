import json
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_db, get_provider_manager
from app.core.security import get_current_user
from app.core.permissions import require_permission
from app.models.user import User
from app.models.agent import Agent
from app.models.chat import Chat, ChatMessage, MessageRole
from app.schemas.chat import ChatCreate, ChatResponse, ChatWithMessages, MessageSend, MessageResponse
from app.schemas.provider import ChatCompletionRequest, ChatCompletionResponse
from app.providers.registry import ProviderManager, ProviderChainExhausted

router = APIRouter()


# ── Database-persisted chat routes (backward compatible) ─────────


@router.get("/", response_model=list[ChatResponse])
async def list_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Chat).where(Chat.user_id == current_user.id).order_by(Chat.updated_at.desc())
    )
    chats = result.scalars().all()
    return [ChatResponse.model_validate(c) for c in chats]


@router.post("/", response_model=ChatResponse, status_code=201)
async def create_chat(
    data: ChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("agents:chat")),
):
    agent_result = await db.execute(
        select(Agent).where(Agent.id == data.agent_id)
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    chat = Chat(
        title=data.title or f"Chat with {agent.name}",
        user_id=current_user.id,
        agent_id=data.agent_id,
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return ChatResponse.model_validate(chat)


@router.get("/{chat_id}", response_model=ChatWithMessages)
async def get_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id,
        )
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at)
    )
    messages = messages_result.scalars().all()

    response = ChatWithMessages.model_validate(chat)
    response.messages = [MessageResponse.model_validate(m) for m in messages]
    return response


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: int,
    data: MessageSend,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("agents:chat")),
    pm: ProviderManager = Depends(get_provider_manager),
):
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id,
        )
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    agent_result = await db.execute(
        select(Agent).where(Agent.id == chat.agent_id)
    )
    agent = agent_result.scalar_one_or_none()

    user_message = ChatMessage(
        chat_id=chat_id,
        role=MessageRole.USER,
        content=data.content,
    )
    db.add(user_message)
    await db.commit()

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at)
    )
    history = messages_result.scalars().all()

    provider_messages = []
    if agent and agent.system_prompt:
        provider_messages.append({"role": "system", "content": agent.system_prompt})

    for msg in history:
        role = "assistant" if msg.role == MessageRole.AGENT else "user"
        provider_messages.append({"role": role, "content": msg.content})

    agent_provider = data.provider or (getattr(agent, "provider", None) if agent else None)
    agent_model = data.model or (agent.model if agent else None)
    agent_temp = agent.temperature if agent else 0.7

    if not data.stream:
        start = time.time()
        try:
            content, usage, used_provider, used_model = await pm.chat(
                messages=provider_messages,
                model=agent_model,
                provider=agent_provider,
                temperature=agent_temp,
                user_id=current_user.id,
            )
        except ProviderChainExhausted as e:
            raise HTTPException(
                status_code=503,
                detail=f"All AI providers unavailable: {e.last_error}",
            )

        agent_message = ChatMessage(
            chat_id=chat_id,
            role=MessageRole.AGENT,
            content=content,
        )
        db.add(agent_message)
        await db.commit()
        await db.refresh(agent_message)

        latency = (time.time() - start) * 1000
        from app.providers.cost_tracker import CostTracker
        tracker = CostTracker(db)
        await tracker.track(
            provider=used_provider,
            model=used_model,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=latency,
            user_id=current_user.id,
            agent_id=agent.id if agent else None,
            chat_id=chat_id,
        )

        return {
            **MessageResponse.model_validate(agent_message).model_dump(),
            "provider": used_provider,
            "model": used_model,
        }

    async def event_generator():
        full_content = ""
        used_provider = None
        used_model = None
        final_usage = {}
        start_time = time.time()

        try:
            async for event in pm.chat_stream(
                messages=provider_messages,
                model=agent_model,
                provider=agent_provider,
                temperature=agent_temp,
                user_id=current_user.id,
            ):
                if event["type"] == "chunk":
                    full_content += event["content"]
                    yield {"event": "chunk", "data": json.dumps({"content": event["content"]})}
                elif event["type"] == "done":
                    used_provider = event["provider"]
                    used_model = event["model"]
                    final_usage = event.get("usage", {})
                elif event["type"] == "error":
                    yield {"event": "error", "data": json.dumps({"error": event["content"]})}
                    return

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
            return

        agent_message = ChatMessage(
            chat_id=chat_id,
            role=MessageRole.AGENT,
            content=full_content,
        )
        db.add(agent_message)
        await db.commit()
        await db.refresh(agent_message)

        latency = (time.time() - start_time) * 1000
        try:
            from app.providers.cost_tracker import CostTracker
            tracker = CostTracker(db)
            await tracker.track(
                provider=used_provider or "unknown",
                model=used_model or "unknown",
                input_tokens=final_usage.get("input_tokens", 0),
                output_tokens=final_usage.get("output_tokens", 0),
                total_tokens=final_usage.get("total_tokens", 0),
                latency_ms=latency,
                user_id=current_user.id,
                agent_id=agent.id if agent else None,
                chat_id=chat_id,
            )
        except Exception:
            pass

        yield {
            "event": "done",
            "data": json.dumps({
                **MessageResponse.model_validate(agent_message).model_dump(),
                "provider": used_provider,
                "model": used_model,
                "usage": final_usage,
            }),
        }

    return EventSourceResponse(event_generator())


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id,
        )
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    await db.execute(
        select(ChatMessage).where(ChatMessage.chat_id == chat_id)
    )
    await db.delete(chat)
    await db.commit()


# ── Unified completions endpoint (no DB persistence) ─────────────


@router.post("/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    req: ChatCompletionRequest,
    current_user: User = Depends(get_current_user),
    pm: ProviderManager = Depends(get_provider_manager),
    db: AsyncSession = Depends(get_db),
):
    if req.stream:
        raise HTTPException(status_code=400, detail="Use POST /chat/completions/stream for streaming")

    try:
        content, usage, used_provider, used_model = await pm.chat(
            messages=req.messages,
            model=req.model,
            provider=req.provider,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            user_id=current_user.id,
        )
    except ProviderChainExhausted as e:
        raise HTTPException(
            status_code=503,
            detail=f"All AI providers unavailable: {e.last_error}",
        )

    from app.providers.cost_tracker import CostTracker
    tracker = CostTracker(db)
    await tracker.track(
        provider=used_provider,
        model=used_model,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        user_id=current_user.id,
        endpoint="completions",
    )

    return ChatCompletionResponse(
        content=content,
        provider=used_provider,
        model=used_model,
        usage=usage,
    )


@router.post("/completions/stream")
async def chat_completions_stream(
    req: ChatCompletionRequest,
    current_user: User = Depends(get_current_user),
    pm: ProviderManager = Depends(get_provider_manager),
    db: AsyncSession = Depends(get_db),
):
    if not req.stream:
        req.stream = True

    async def event_generator():
        full_content = ""
        used_provider = None
        used_model = None
        final_usage = {}

        async for event in pm.chat_stream(
            messages=req.messages,
            model=req.model,
            provider=req.provider,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            user_id=current_user.id,
        ):
            if event["type"] == "chunk":
                full_content += event["content"]
                yield {"event": "chunk", "data": json.dumps({"content": event["content"]})}
            elif event["type"] == "done":
                used_provider = event["provider"]
                used_model = event["model"]
                final_usage = event.get("usage", {})
                yield {
                    "event": "done",
                    "data": json.dumps({
                        "content": full_content,
                        "provider": used_provider,
                        "model": used_model,
                        "usage": final_usage,
                    }),
                }
            elif event["type"] == "error":
                yield {"event": "error", "data": json.dumps({"error": event["content"]})}
                return

        if used_provider:
            try:
                from app.providers.cost_tracker import CostTracker
                tracker = CostTracker(db)
                await tracker.track(
                    provider=used_provider,
                    model=used_model or "unknown",
                    input_tokens=final_usage.get("input_tokens", 0),
                    output_tokens=final_usage.get("output_tokens", 0),
                    total_tokens=final_usage.get("total_tokens", 0),
                    user_id=current_user.id,
                    endpoint="completions_stream",
                )
            except Exception:
                pass

    return EventSourceResponse(event_generator())
