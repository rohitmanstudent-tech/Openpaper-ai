import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_live(client: AsyncClient):
    resp = await client.get("/api/v1/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "alive"
    assert "version" in data
    assert "timestamp" in data
    assert data["app"] == "OpenPaper AI"


@pytest.mark.asyncio
async def test_health_ready_structure(client: AsyncClient):
    resp = await client.get("/api/v1/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]
    assert "uptime_seconds" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_deep_structure(client: AsyncClient):
    resp = await client.get("/api/v1/health/deep")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]
    assert "providers" in data["checks"]


@pytest.mark.asyncio
async def test_health_legacy_endpoint(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "alive"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_live_response_time(client: AsyncClient):
    import time

    start = time.monotonic()
    for _ in range(10):
        await client.get("/api/v1/health/live")
    elapsed = time.monotonic() - start
    assert elapsed < 5.0, f"10 rapid health checks took {elapsed:.2f}s, expected < 5s"


@pytest.mark.asyncio
async def test_health_ready_uptime_increasing(client: AsyncClient):
    resp1 = await client.get("/api/v1/health/ready")
    import asyncio

    await asyncio.sleep(0.1)
    resp2 = await client.get("/api/v1/health/ready")
    u1 = resp1.json()["uptime_seconds"]
    u2 = resp2.json()["uptime_seconds"]
    assert u2 >= u1, f"uptime decreased: {u2} < {u1}"
