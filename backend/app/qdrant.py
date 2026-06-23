from qdrant_client import AsyncQdrantClient
from app.config import get_settings

settings = get_settings()

qdrant_client: AsyncQdrantClient = AsyncQdrantClient(
    url=settings.QDRANT_URL,
    prefer_grpc=True,
)


async def get_qdrant() -> AsyncQdrantClient:
    return qdrant_client


async def init_qdrant():
    collections = await qdrant_client.get_collections()
    existing = [c.name for c in collections.collections]

    if "documents" not in existing:
        await qdrant_client.create_collection(
            collection_name="documents",
            vectors_config={"size": 1536, "distance": "Cosine"},
        )

    if "memories" not in existing:
        await qdrant_client.create_collection(
            collection_name="memories",
            vectors_config={"size": 1536, "distance": "Cosine"},
        )
