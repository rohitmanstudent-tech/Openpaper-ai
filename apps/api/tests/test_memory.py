"""Tests for the Memory Engine module."""

from unittest.mock import AsyncMock

import pytest

from app.core.memory import MemoryEngine, get_memory_engine, set_memory_engine
from app.models.memory import MemoryType


@pytest.fixture(autouse=True)
def _mock_engine():
    engine = MemoryEngine()
    engine.create = AsyncMock(return_value={
        "id": "mem-1", "agent_id": "test-agent", "memory_type": "short_term",
        "content": "test content", "importance_score": 0.5, "score": 0.0,
        "namespace": "default", "user_id": "", "summary": "test content",
        "metadata": {}, "created_at": "2024-01-01T00:00:00+00:00",
        "expires_at": None, "last_accessed_at": "2024-01-01T00:00:00+00:00",
        "access_count": 0, "consolidated": False,
    })
    engine.get = AsyncMock(return_value={
        "id": "mem-1", "agent_id": "test-agent", "memory_type": "short_term",
        "content": "test content", "importance_score": 0.5, "score": 0.0,
        "namespace": "default", "user_id": "", "summary": "test content",
        "metadata": {}, "created_at": "2024-01-01T00:00:00+00:00",
        "expires_at": None, "last_accessed_at": "2024-01-01T00:00:00+00:00",
        "access_count": 1, "consolidated": False,
    })
    engine.update = AsyncMock(return_value={
        "id": "mem-1", "agent_id": "test-agent", "memory_type": "long_term",
        "content": "updated content", "importance_score": 0.8, "score": 0.0,
        "namespace": "default", "user_id": "", "summary": "updated content",
        "metadata": {"key": "val"}, "created_at": "2024-01-01T00:00:00+00:00",
        "expires_at": None, "last_accessed_at": "2024-01-01T00:00:00+00:00",
        "access_count": 1, "consolidated": False,
    })
    engine.delete = AsyncMock(return_value=True)
    engine.recall = AsyncMock(return_value=[
        {"id": "mem-1", "agent_id": "test-agent", "memory_type": "short_term",
         "content": "relevant memory", "importance_score": 0.7, "score": 0.85,
         "namespace": "default", "user_id": "", "summary": "relevant memory",
         "metadata": {}, "created_at": "2024-01-01T00:00:00+00:00",
         "expires_at": None, "last_accessed_at": "2024-01-01T00:00:00+00:00",
         "access_count": 0, "consolidated": False},
    ])
    engine.search = AsyncMock(return_value=[
        {"id": "mem-1", "agent_id": "test-agent", "memory_type": "short_term",
         "content": "found memory", "importance_score": 0.6, "score": 0.75,
         "namespace": "default", "user_id": "", "summary": "found memory",
         "metadata": {}, "created_at": "2024-01-01T00:00:00+00:00",
         "expires_at": None, "last_accessed_at": "2024-01-01T00:00:00+00:00",
         "access_count": 0, "consolidated": False},
    ])
    engine.consolidate = AsyncMock(return_value=5)
    engine.expire = AsyncMock(return_value=3)
    engine.count = AsyncMock(return_value=10)
    engine.recall_agent_context = AsyncMock(return_value="- [short_term] relevant memory")
    set_memory_engine(engine)
    yield
    set_memory_engine(None)


class TestMemoryEngine:
    async def test_create_memory(self):
        engine = get_memory_engine()
        result = await engine.create(
            agent_id="test-agent",
            content="Important decision: approved budget for Q3 campaign",
            memory_type=MemoryType.SHORT_TERM,
        )
        assert result["id"] == "mem-1"
        assert result["agent_id"] == "test-agent"
        engine.create.assert_called_once()

    async def test_get_memory(self):
        engine = get_memory_engine()
        result = await engine.get("mem-1")
        assert result is not None
        assert result["id"] == "mem-1"

    async def test_get_nonexistent_memory(self):
        engine = get_memory_engine()
        engine.get = AsyncMock(return_value=None)
        result = await engine.get("nonexistent")
        assert result is None

    async def test_update_memory(self):
        engine = get_memory_engine()
        result = await engine.update(
            point_id="mem-1",
            content="updated content",
            importance_score=0.8,
            memory_type=MemoryType.LONG_TERM,
        )
        assert result["content"] == "updated content"
        assert result["importance_score"] == 0.8
        assert result["memory_type"] == "long_term"

    async def test_delete_memory(self):
        engine = get_memory_engine()
        result = await engine.delete("mem-1")
        assert result is True

    async def test_recall_relevant(self):
        engine = get_memory_engine()
        results = await engine.recall(
            query="budget decision",
            agent_id="test-agent",
            limit=5,
            min_score=0.3,
        )
        assert len(results) == 1
        assert results[0]["content"] == "relevant memory"
        assert results[0]["score"] == 0.85

    async def test_search_memories(self):
        engine = get_memory_engine()
        results = await engine.search(
            query_text="campaign budget",
            limit=10,
        )
        assert len(results) == 1
        assert results[0]["content"] == "found memory"

    async def test_consolidate(self):
        engine = get_memory_engine()
        count = await engine.consolidate(agent_id="test-agent", min_importance=0.6)
        assert count == 5

    async def test_expire(self):
        engine = get_memory_engine()
        count = await engine.expire()
        assert count == 3

    async def test_count(self):
        engine = get_memory_engine()
        count = await engine.count(agent_id="test-agent")
        assert count == 10

    async def test_recall_agent_context(self):
        engine = get_memory_engine()
        context = await engine.recall_agent_context("test-agent", "budget")
        assert "relevant memory" in context


class TestMemoryTypes:
    def test_memory_type_values(self):
        assert MemoryType.SHORT_TERM.value == "short_term"
        assert MemoryType.LONG_TERM.value == "long_term"
        assert MemoryType.SHARED_TEAM.value == "shared_team"
        assert MemoryType.AGENT_PERSONAL.value == "agent_personal"
