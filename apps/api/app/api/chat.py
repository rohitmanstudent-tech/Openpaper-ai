import json

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ProviderError
from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.models.agent import Agent, Chat, ChatMessage
from app.providers import get_provider
from app.schemas.chat import ChatCreate, ChatResponse, ChatWithMessages, MessageResponse, MessageSend

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/chats", response_model=list[ChatResponse])
async def list_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Chat).where(Chat.user_id == current_user.id).order_by(Chat.updated_at.desc()))
    return [ChatResponse.model_validate(c) for c in result.scalars().all()]


@router.post("/chats", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    data: ChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = Chat(
        title=data.title or f"Chat with agent {data.agent_id}",
        agent_id=data.agent_id,
        user_id=current_user.id,
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return ChatResponse.model_validate(chat)


@router.get("/chats/{chat_id}", response_model=ChatWithMessages)
async def get_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == current_user.id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise NotFoundError("Chat not found")

    msg_result = await db.execute(
        select(ChatMessage).where(ChatMessage.chat_id == chat_id).order_by(ChatMessage.created_at)
    )
    messages = msg_result.scalars().all()
    chat_data = ChatResponse.model_validate(chat)
    return ChatWithMessages(**chat_data.model_dump(), messages=[MessageResponse.model_validate(m) for m in messages])


@router.post("/chats/{chat_id}/messages", response_model=MessageResponse)
async def send_message(
    chat_id: int,
    data: MessageSend,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == current_user.id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise NotFoundError("Chat not found")
    msg = ChatMessage(chat_id=chat_id, role="user", content=data.content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return MessageResponse.model_validate(msg)


@router.post("/chats/{chat_id}/completions")
async def chat_completion(
    chat_id: int,
    data: MessageSend,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == current_user.id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise NotFoundError("Chat not found")

    agent_result = await db.execute(select(Agent).where(Agent.id == chat.agent_id))
    agent = agent_result.scalar_one_or_none()

    msg = ChatMessage(chat_id=chat_id, role="user", content=data.content)
    db.add(msg)
    await db.commit()

    msg_result = await db.execute(
        select(ChatMessage).where(ChatMessage.chat_id == chat_id).order_by(ChatMessage.created_at)
    )
    all_messages = msg_result.scalars().all()

    messages = [{"role": m.role, "content": m.content} for m in all_messages]
    if agent and agent.system_prompt:
        messages.insert(0, {"role": "system", "content": agent.system_prompt})

    provider_name = agent.provider if agent else "ollama"
    model = agent.model if agent else None
    provider = get_provider(provider_name)

    if not provider:
        raise ProviderError(f"Provider '{provider_name}' is not available")

    if data.stream:

        async def generate():
            full_content = ""
            async for chunk in provider.chat_stream(messages, model=model):
                full_content += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            assistant_msg = ChatMessage(chat_id=chat_id, role="agent", content=full_content)
            db.add(assistant_msg)
            await db.commit()
            yield f"data: {json.dumps({'done': True, 'message_id': assistant_msg.id})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        content = await provider.chat(messages, model=model)
        assistant_msg = ChatMessage(chat_id=chat_id, role="agent", content=content)
        db.add(assistant_msg)
        await db.commit()
        await db.refresh(assistant_msg)
        return MessageResponse.model_validate(assistant_msg)
