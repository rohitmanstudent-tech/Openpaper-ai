"""Qdrant vector store service for semantic search and agent memory.

Provides async CRUD operations, collection management, and filtered
semantic search backed by Qdrant.
"""

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import get_settings
from app.core.embedding import get_embedding_provider

logger = logging.getLogger(__name__)

_client: QdrantClient | None = None
_initialized = False

# ── Default collection config ────────────────────────────────────────────
DEFAULT_COLLECTION_NAME = "agent_memories"
EVENTS_COLLECTION_NAME = "agent_events"
PAYLOAD_INDEXES = [
    ("agent_id", qmodels.PayloadSchemaType.KEYWORD),
    ("user_id", qmodels.PayloadSchemaType.KEYWORD),
    ("namespace", qmodels.PayloadSchemaType.KEYWORD),
    ("memory_type", qmodels.PayloadSchemaType.KEYWORD),
    ("created_at", qmodels.PayloadSchemaType.FLOAT),
]

EVENTS_PAYLOAD_INDEXES = [
    ("event_type", qmodels.PayloadSchemaType.KEYWORD),
    ("source_agent", qmodels.PayloadSchemaType.KEYWORD),
    ("target_agent", qmodels.PayloadSchemaType.KEYWORD),
    ("correlation_id", qmodels.PayloadSchemaType.KEYWORD),
    ("timestamp", qmodels.PayloadSchemaType.FLOAT),
]


# ── Initialization ───────────────────────────────────────────────────────


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        settings = get_settings()
        if settings.QDRANT_API_KEY:
            _client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=30,
            )
        else:
            _client = QdrantClient(
                location=settings.QDRANT_URL.replace("http://", "").replace("https://", ""),
                timeout=30,
            )
    return _client


async def init_vector_store() -> None:
    global _initialized
    try:
        client = get_client()
        emb = get_embedding_provider()
        collections = client.get_collections().collections
        names = [c.name for c in collections]

        for col_name in [DEFAULT_COLLECTION_NAME, EVENTS_COLLECTION_NAME]:
            if col_name not in names:
                client.create_collection(
                    collection_name=col_name,
                    vectors_config=qmodels.VectorParams(
                        size=emb.dimension,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
                indexes = EVENTS_PAYLOAD_INDEXES if col_name == EVENTS_COLLECTION_NAME else PAYLOAD_INDEXES
                for field, schema in indexes:
                    client.create_payload_index(
                        collection_name=col_name,
                        field_name=field,
                        field_schema=schema,
                    )
                logger.info("Created Qdrant collection '%s' (dim=%d)", col_name, emb.dimension)

        _initialized = True
        logger.info("Qdrant vector store initialized")
    except Exception as e:
        logger.warning("Qdrant init failed (is Qdrant running?): %s", e)
        _initialized = False


async def close_vector_store() -> None:
    global _client, _initialized
    if _client:
        _client.close()
        _client = None
    _initialized = False


# ── CRUD Operations ─────────────────────────────────────────────────────


async def upsert_point(
    collection: str,
    point_id: str,
    vector: list[float] | None = None,
    payload: dict[str, Any] | None = None,
    text: str | None = None,
) -> str:
    """Insert or update a vector point.

    If vector is None and text is given, generates embedding automatically.
    """
    if vector is None and text is not None:
        emb = get_embedding_provider()
        vector = await emb.embed(text)

    if vector is None:
        raise ValueError("Either vector or text must be provided")

    client = get_client()
    client.upsert(
        collection_name=collection,
        points=[qmodels.PointStruct(id=point_id, vector=vector, payload=payload or {})],
    )
    return point_id


async def delete_point(collection: str, point_id: str) -> bool:
    client = get_client()
    client.delete(
        collection_name=collection,
        points_selector=qmodels.PointIdsList(points=[point_id]),
    )
    return True


async def get_point(collection: str, point_id: str) -> dict[str, Any] | None:
    client = get_client()
    points = client.retrieve(
        collection_name=collection,
        ids=[point_id],
        with_payload=True,
        with_vectors=False,
    )
    if not points:
        return None
    p = points[0]
    return {"id": p.id, "payload": p.payload or {}}


async def count_points(collection: str) -> int:
    client = get_client()
    result = client.count(collection_name=collection)
    return result.count


# ── Search ────────────────────────────────────────────────────────────────


async def search(
    collection: str,
    query_text: str | None = None,
    query_vector: list[float] | None = None,
    filters: dict[str, Any] | None = None,
    limit: int = 10,
    score_threshold: float | None = None,
) -> list[dict[str, Any]]:
    """Semantic search with optional metadata filtering."""
    if query_vector is None and query_text is not None:
        emb = get_embedding_provider()
        query_vector = await emb.embed(query_text)

    if query_vector is None:
        raise ValueError("Either query_vector or query_text must be provided")

    client = get_client()
    qfilter = _build_filter(filters) if filters else None

    results = client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=limit,
        query_filter=qfilter,
        score_threshold=score_threshold,
        with_payload=True,
    )

    return [
        {
            "id": r.id,
            "score": r.score,
            "payload": r.payload or {},
        }
        for r in results
    ]


async def scroll(
    collection: str,
    filters: dict[str, Any] | None = None,
    limit: int = 100,
    offset: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Scroll through points with optional filtering."""
    client = get_client()
    qfilter = _build_filter(filters) if filters else None

    results, next_offset = client.scroll(
        collection_name=collection,
        limit=limit,
        offset=offset,
        filter=qfilter,
        with_payload=True,
        with_vectors=False,
    )

    return (
        [{"id": r.id, "payload": r.payload or {}} for r in results],
        next_offset,
    )


# ── Collection Management ────────────────────────────────────────────────


async def list_collections() -> list[str]:
    client = get_client()
    collections = client.get_collections().collections
    return [c.name for c in collections]


async def delete_collection(name: str) -> bool:
    client = get_client()
    client.delete_collection(collection_name=name)
    return True


async def recreate_collection(name: str) -> bool:
    await delete_collection(name)
    emb = get_embedding_provider()
    client = get_client()
    client.create_collection(
        collection_name=name,
        vectors_config=qmodels.VectorParams(
            size=emb.dimension,
            distance=qmodels.Distance.COSINE,
        ),
    )
    for field, schema in PAYLOAD_INDEXES:
        client.create_payload_index(
            collection_name=name,
            field_name=field,
            field_schema=schema,
        )
    return True


async def vector_store_health() -> dict[str, Any]:
    """Check Qdrant connectivity and return collection info."""
    try:
        client = get_client()
        info = client.get_collections()
        collections = [c.name for c in info.collections]
        return {
            "status": "available",
            "collections": collections,
            "default_collection": DEFAULT_COLLECTION_NAME,
        }
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


# ── Helpers ──────────────────────────────────────────────────────────────


def _build_filter(filters: dict[str, Any]) -> qmodels.Filter:
    """Convert a flat dict of {field: value} into a Qdrant Filter.

    Supports $gt, $gte, $lt, $lte, $ne, $in operators in values.
    """
    must_conditions = []
    for field, value in filters.items():
        if isinstance(value, dict):
            for op, v in value.items():
                if op == "$gt":
                    must_conditions.append(qmodels.FieldCondition(key=field, range=qmodels.Range(gt=v)))
                elif op == "$gte":
                    must_conditions.append(qmodels.FieldCondition(key=field, range=qmodels.Range(gte=v)))
                elif op == "$lt":
                    must_conditions.append(qmodels.FieldCondition(key=field, range=qmodels.Range(lt=v)))
                elif op == "$lte":
                    must_conditions.append(qmodels.FieldCondition(key=field, range=qmodels.Range(lte=v)))
                elif op == "$ne":
                    must_conditions.append(
                        qmodels.FieldCondition(key=field, match=qmodels.MatchExcept(**{"except": [v]}))
                    )
                elif op == "$in":
                    must_conditions.append(qmodels.FieldCondition(key=field, match=qmodels.MatchAny(any=v)))
        else:
            must_conditions.append(qmodels.FieldCondition(key=field, match=qmodels.MatchValue(value=value)))

    return qmodels.Filter(must=must_conditions) if must_conditions else qmodels.Filter()
