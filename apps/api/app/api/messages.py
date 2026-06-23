from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.models.agent import Chat, ChatMessage
from app.schemas.chat import MessageResponse

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ChatMessage).where(ChatMessage.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise NotFoundError("Message not found")

    chat_result = await db.execute(
        select(Chat).where(Chat.id == msg.chat_id, Chat.user_id == current_user.id)
    )
    if not chat_result.scalar_one_or_none():
        raise PermissionDeniedError("Access denied")

    return MessageResponse.model_validate(msg)
