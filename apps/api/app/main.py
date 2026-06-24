import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.agent_graph import router as agent_graph_router
from app.api.agents import router as agents_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.bus import router as bus_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.hub_registry import router as hub_registry_router
from app.api.marketplace import router as marketplace_router
from app.api.memory import router as memory_router
from app.api.messages import router as messages_router
from app.api.models import router as models_router
from app.api.plugins import router as plugins_router
from app.api.providers import router as providers_router
from app.api.tasks import router as tasks_router
from app.api.vectors import router as vectors_router
from app.api.workflows import router as workflows_router
from app.config import get_settings
from app.core.encryption import init_encryption
from app.core.error_middleware import ExceptionMiddleware, RequestIDMiddleware
from app.core.event_bus import get_bus
from app.core.health import mark_startup
from app.core.logging_middleware import LoggingMiddleware, setup_json_logging
from app.core.plugin_registry import get_plugin_registry
from app.core.rate_limiter import RateLimitMiddleware
from app.core.security_middleware import SecurityHeadersMiddleware
from app.core.sentry import init_sentry
from app.core.validator import run_validation
from app.core.vector import init_vector_store
from app.database import init_db
from app.providers import register_providers

settings = get_settings()

# ── Structured JSON Logging ─────────────────
setup_json_logging(settings.LOG_LEVEL)
logger = logging.getLogger("openpaper")


@asynccontextmanager
async def lifespan(app: FastAPI):
    mark_startup()
    run_validation(exit_on_error=False)
    init_sentry()
    init_encryption()
    await init_db()
    register_providers()
    await init_vector_store()
    bus = get_bus()
    await bus.start()
    registry = get_plugin_registry()
    registry.discover_and_load()
    logger.info("OpenPaper AI v%s started", settings.VERSION)
    yield
    logger.info("OpenPaper AI shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)


async def starlette_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR",
            "message": exc.detail,
            "request_id": request_id,
        },
    )


app.add_exception_handler(StarletteHTTPException, starlette_exception_handler)

app.add_middleware(ExceptionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    default_max=settings.RATE_LIMIT_DEFAULT,
    default_window=settings.RATE_LIMIT_WINDOW,
    strict_routes={
        "/api/v1/auth/login": (10, 60),
        "/api/v1/auth/register": (5, 60),
        "/api/v1/auth/refresh": (10, 60),
    },
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(agents_router, prefix="/api/v1", tags=["agents"])
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
app.include_router(messages_router, prefix="/api/v1", tags=["messages"])
app.include_router(providers_router, prefix="/api/v1", tags=["providers"])
app.include_router(models_router, prefix="/api/v1", tags=["models"])
app.include_router(tasks_router, prefix="/api/v1", tags=["tasks"])
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(vectors_router, tags=["vectors"])
app.include_router(memory_router, tags=["memory"])
app.include_router(bus_router, tags=["bus"])
app.include_router(plugins_router, tags=["plugins"])
app.include_router(documents_router, tags=["documents"])
app.include_router(workflows_router, tags=["workflows"])
app.include_router(agent_graph_router, tags=["agent-graph"])
app.include_router(analytics_router, tags=["analytics"])
app.include_router(marketplace_router, tags=["marketplace"])
app.include_router(hub_registry_router, tags=["hub"])


@app.get("/api/health")
async def health():
    from app.core.health import liveness

    return await liveness()
