from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

from app.config import get_settings
from app.core.redis import redis_client
from app.database import engine
from app.providers import get_providers

settings = get_settings()

_start_time: datetime | None = None


def mark_startup() -> None:
    global _start_time
    _start_time = datetime.now(UTC)


def get_uptime() -> float:
    if _start_time is None:
        return 0.0
    return (datetime.now(UTC) - _start_time).total_seconds()


async def check_database() -> dict[str, Any]:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "message": "PostgreSQL reachable"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


async def check_redis() -> dict[str, Any]:
    try:
        if redis_client is None:
            return {"status": "unhealthy", "message": "Redis not initialized"}
        await redis_client.ping()
        return {"status": "healthy", "message": "Redis reachable"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


async def check_providers() -> dict[str, Any]:
    providers = get_providers()
    results = {}
    for name, provider in providers.items():
        try:
            ok = await provider.check_health()
            results[name] = "available" if ok else "unavailable"
        except Exception as e:
            results[name] = f"error: {str(e)}"
    return {
        "status": "healthy" if any(v == "available" for v in results.values()) else "degraded",
        "providers": results,
    }


async def liveness() -> dict[str, Any]:
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": settings.VERSION,
        "app": settings.APP_NAME,
    }


async def check_vector_store() -> dict[str, Any]:
    from app.core.vector import vector_store_health

    result = await vector_store_health()
    if result["status"] == "available":
        return {"status": "healthy", "message": f"Qdrant reachable ({len(result['collections'])} collections)"}
    return {"status": "unhealthy", "message": result.get("error", "Qdrant unavailable")}


async def readiness() -> dict[str, Any]:
    db = await check_database()
    redis_check = await check_redis()
    all_healthy = db["status"] == "healthy" and redis_check["status"] == "healthy"
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": {
            "database": db,
            "redis": redis_check,
        },
        "uptime_seconds": get_uptime(),
        "version": settings.VERSION,
    }


async def deep_check() -> dict[str, Any]:
    db = await check_database()
    redis_check = await check_redis()
    providers = await check_providers()
    vector = await check_vector_store()
    all_healthy = db["status"] == "healthy" and redis_check["status"] == "healthy"
    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": settings.VERSION,
        "environment": "production" if not settings.DEBUG else "development",
        "uptime_seconds": get_uptime(),
        "checks": {
            "database": db,
            "redis": redis_check,
            "providers": providers,
            "vector_store": vector,
        },
    }
