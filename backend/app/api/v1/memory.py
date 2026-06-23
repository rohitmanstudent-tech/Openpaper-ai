from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_provider_manager
from app.core.security import get_current_user
from app.models.user import User
from app.models.memory import Memory
from app.schemas.memory import MemoryCreate, MemoryResponse, MemorySearch
from app.services.memory import MemoryService
from app.providers.registry import ProviderManager

router = APIRouter()


@router.post("/", response_model=MemoryResponse, status_code=201)
async def create_memory(
    data: MemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pm: ProviderManager = Depends(get_provider_manager),
):
    service = MemoryService(db, pm)
    memory = await service.create_memory(data, current_user.id)
    return MemoryResponse.model_validate(memory)


@router.get("/", response_model=list[MemoryResponse])
async def list_memories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Memory)
        .where(Memory.user_id == current_user.id)
        .order_by(Memory.created_at.desc())
        .limit(50)
    )
    memories = result.scalars().all()
    return [MemoryResponse.model_validate(m) for m in memories]


@router.post("/search", response_model=list[MemoryResponse])
async def search_memories(
    data: MemorySearch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pm: ProviderManager = Depends(get_provider_manager),
):
    service = MemoryService(db, pm)
    memories = await service.search_memories(
        query=data.query,
        user_id=current_user.id,
        scope=data.scope,
        limit=data.limit,
    )
    return [MemoryResponse.model_validate(m) for m in memories]


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pm: ProviderManager = Depends(get_provider_manager),
):
    service = MemoryService(db, pm)
    deleted = await service.delete_memory(memory_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
