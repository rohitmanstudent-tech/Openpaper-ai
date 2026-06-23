import json
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.memory import Memory, MemoryScope, MemoryType
from app.schemas.memory import MemoryCreate
from app.providers.registry import ProviderManager
from app.qdrant import get_qdrant
from app.config import get_settings


class MemoryService:
    def __init__(self, db: AsyncSession, provider_manager: ProviderManager):
        self.db = db
        self.provider_manager = provider_manager

    async def _generate_embedding(self, text: str) -> list[float]:
        settings = get_settings()
        ollama_url = f"{settings.OLLAMA_BASE_URL}/api/embeddings"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    ollama_url,
                    json={"model": "nomic-embed-text", "prompt": text},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("embedding", [])
        except Exception:
            return []

    async def create_memory(self, data: MemoryCreate, user_id: int) -> Memory:
        embedding = await self._generate_embedding(data.content)

        memory = Memory(
            content=data.content,
            memory_type=data.memory_type,
            scope=data.scope,
            user_id=user_id,
            agent_id=data.agent_id,
            source=data.source,
            tags=data.tags,
        )
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)

        qdrant = await get_qdrant()
        point_id = f"memory_{memory.id}"
        try:
            await qdrant.upsert(
                collection_name="memories",
                points=[
                    {
                        "id": point_id,
                        "vector": embedding,
                        "payload": {
                            "memory_id": memory.id,
                            "user_id": user_id,
                            "agent_id": data.agent_id or "",
                            "scope": data.scope,
                            "content": data.content,
                            "tags": data.tags or "",
                        },
                    }
                ],
            )
            memory.embedding_id = point_id
        except Exception:
            pass

        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def search_memories(
        self, query: str, user_id: int, scope: str | None = None, limit: int = 10
    ) -> list[Memory]:
        embedding = await self._generate_embedding(query)
        if not embedding:
            return []

        qdrant = await get_qdrant()
        search_filter = {"must": [{"key": "user_id", "match": {"value": user_id}}]}
        if scope:
            search_filter["must"].append(
                {"key": "scope", "match": {"value": scope}}
            )

        try:
            results = await qdrant.search(
                collection_name="memories",
                query_vector=embedding,
                query_filter=search_filter,
                limit=limit,
            )
        except Exception:
            return []

        memory_ids = [int(r.payload["memory_id"]) for r in results if r.payload.get("memory_id")]
        if not memory_ids:
            return []

        result = await self.db.execute(
            select(Memory).where(Memory.id.in_(memory_ids))
        )
        return list(result.scalars().all())

    async def get_agent_memories(self, agent_id: int, limit: int = 50) -> list[Memory]:
        result = await self.db.execute(
            select(Memory)
            .where(
                (Memory.agent_id == agent_id) |
                (Memory.scope == MemoryScope.TEAM) |
                (Memory.scope == MemoryScope.GLOBAL)
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_memory(self, memory_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(Memory).where(
                Memory.id == memory_id,
                Memory.user_id == user_id,
            )
        )
        memory = result.scalar_one_or_none()
        if not memory:
            return False

        qdrant = await get_qdrant()
        if memory.embedding_id:
            try:
                await qdrant.delete(
                    collection_name="memories",
                    points_selector={"points": [memory.embedding_id]},
                )
            except Exception:
                pass

        await self.db.delete(memory)
        await self.db.commit()
        return True
