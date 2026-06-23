from fastapi import APIRouter

from app.core.health import deep_check, liveness, readiness

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def health_live():
    return await liveness()


@router.get("/ready")
async def health_ready():
    return await readiness()


@router.get("/deep")
async def health_deep():
    return await deep_check()
