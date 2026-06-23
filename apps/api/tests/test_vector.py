"""Tests for the Qdrant vector store module."""

import pytest

from app.core.embedding import EmbeddingProvider, set_embedding_provider
from app.core.vector import (
    DEFAULT_COLLECTION_NAME,
    close_vector_store,
    count_points,
    delete_point,
    get_point,
    init_vector_store,
    list_collections,
    recreate_collection,
    scroll,
    search,
    upsert_point,
    vector_store_health,
)


class FakeEmbeddingProvider(EmbeddingProvider):
    """Returns deterministic embeddings for testing."""

    @property
    def dimension(self) -> int:
        return 4

    @property
    def name(self) -> str:
        return "test/fake"

    async def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3, 0.4]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


@pytest.fixture(autouse=True)
def _fake_embedding():
    set_embedding_provider(FakeEmbeddingProvider())
    yield


@pytest.fixture(autouse=True)
async def _setup_vector():
    try:
        await init_vector_store()
        yield
        await close_vector_store()
    except Exception:
        pytest.skip("Qdrant not available — skipping vector tests")


class TestVectorStore:
    """Requires Qdrant running on localhost:6333."""

    @pytest.mark.skipif(True, reason="Requires Qdrant at localhost:6333")
    async def test_health_available(self):
        health = await vector_store_health()
        assert health["status"] == "available"
        assert DEFAULT_COLLECTION_NAME in health["collections"]

    @pytest.mark.skipif(True, reason="Requires Qdrant at localhost:6333")
    async def test_upsert_and_retrieve(self):
        pid = "test-1"
        await upsert_point(
            collection=DEFAULT_COLLECTION_NAME,
            point_id=pid,
            vector=[0.1, 0.2, 0.3, 0.4],
            payload={"agent_id": "agent-1", "text": "hello world"},
        )
        point = await get_point(DEFAULT_COLLECTION_NAME, pid)
        assert point is not None
        assert point["id"] == pid
        assert point["payload"]["agent_id"] == "agent-1"

    @pytest.mark.skipif(True, reason="Requires Qdrant at localhost:6333")
    async def test_search_by_text(self):
        pid = "test-search"
        await upsert_point(
            collection=DEFAULT_COLLECTION_NAME,
            point_id=pid,
            text="machine learning transformer model",
            payload={"agent_id": "agent-1", "memory_type": "observation"},
        )
        results = await search(
            collection=DEFAULT_COLLECTION_NAME,
            query_text="AI training",
            limit=5,
        )
        assert len(results) > 0
        assert any(r["id"] == pid for r in results)

    @pytest.mark.skipif(True, reason="Requires Qdrant at localhost:6333")
    async def test_search_with_filter(self):
        pid = "test-filter"
        pid2 = "test-filter-2"
        await upsert_point(
            collection=DEFAULT_COLLECTION_NAME,
            point_id=pid,
            text="customer inquiry about pricing",
            payload={"agent_id": "agent-1", "memory_type": "message", "user_id": "user-1"},
        )
        await upsert_point(
            collection=DEFAULT_COLLECTION_NAME,
            point_id=pid2,
            text="internal team brainstorming",
            payload={"agent_id": "agent-2", "memory_type": "thought", "user_id": "user-1"},
        )
        results = await search(
            collection=DEFAULT_COLLECTION_NAME,
            query_text="pricing inquiry",
            filters={"agent_id": "agent-1"},
            limit=10,
        )
        assert len(results) > 0
        assert all(r["payload"]["agent_id"] == "agent-1" for r in results)

    @pytest.mark.skipif(True, reason="Requires Qdrant at localhost:6333")
    async def test_delete_point(self):
        pid = "test-delete"
        await upsert_point(
            collection=DEFAULT_COLLECTION_NAME,
            point_id=pid,
            vector=[0.1, 0.2, 0.3, 0.4],
            payload={},
        )
        await delete_point(DEFAULT_COLLECTION_NAME, pid)
        point = await get_point(DEFAULT_COLLECTION_NAME, pid)
        assert point is None

    @pytest.mark.skipif(True, reason="Requires Qdrant at localhost:6333")
    async def test_count(self):
        await upsert_point(
            collection=DEFAULT_COLLECTION_NAME,
            point_id="count-1",
            vector=[0.1, 0.2, 0.3, 0.4],
            payload={},
        )
        count = await count_points(DEFAULT_COLLECTION_NAME)
        assert isinstance(count, int)
        assert count > 0

    @pytest.mark.skipif(True, reason="Requires Qdrant at localhost:6333")
    async def test_scroll(self):
        points, next_offset = await scroll(
            collection=DEFAULT_COLLECTION_NAME,
            filters={"agent_id": "agent-1"},
            limit=10,
        )
        assert isinstance(points, list)
        assert isinstance(next_offset, (str, type(None)))

    @pytest.mark.skipif(True, reason="Requires Qdrant at localhost:6333")
    async def test_list_and_recreate_collection(self):
        collections = await list_collections()
        assert DEFAULT_COLLECTION_NAME in collections

        test_col = "_test_temp"
        await recreate_collection(test_col)
        collections = await list_collections()
        assert test_col in collections

    @pytest.mark.skipif(True, reason="Requires Qdrant at localhost:6333")
    async def test_upsert_with_text_auto_embed(self):
        pid = "test-auto-embed"
        await upsert_point(
            collection=DEFAULT_COLLECTION_NAME,
            point_id=pid,
            text="this is a test of automatic embedding",
            payload={"agent_id": "agent-3"},
        )
        point = await get_point(DEFAULT_COLLECTION_NAME, pid)
        assert point is not None
        assert point["payload"]["agent_id"] == "agent-3"


class TestFakeEmbedding:
    def test_dimension(self):
        provider = FakeEmbeddingProvider()
        assert provider.dimension == 4

    def test_name(self):
        provider = FakeEmbeddingProvider()
        assert provider.name == "test/fake"
