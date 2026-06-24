"""Structured JSON logging with correlation ID injection,
request tracing, workflow tracing, and agent tracing.

Usage:
    from app.core.logging_middleware import LoggingMiddleware, get_correlation_id
    app.add_middleware(LoggingMiddleware)

    # In any handler:
    logger.info("Processing request", extra={"correlation_id": get_correlation_id()})
"""

import json
import logging
import re
import sys
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

try:
    from contextvars import ContextVar

    _correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
    _workflow_id: ContextVar[str] = ContextVar("workflow_id", default="")
    _agent_id: ContextVar[str] = ContextVar("agent_id", default="")
    _request_path: ContextVar[str] = ContextVar("request_path", default="")
    _request_method: ContextVar[str] = ContextVar("request_method", default="")
except ImportError:
    _correlation_id = None
    _workflow_id = None
    _agent_id = None
    _request_path = None
    _request_method = None


SANITIZE_HEADERS = {
    "authorization",
    "x-api-key",
    "cookie",
    "set-cookie",
    "x-auth-token",
    "proxy-authorization",
}

SENSITIVE_FIELD_PATTERNS = [
    re.compile(r"api_key", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"key", re.IGNORECASE),
    re.compile(r"credit_card", re.IGNORECASE),
    re.compile(r"ssn", re.IGNORECASE),
]


def get_correlation_id() -> str:
    if _correlation_id:
        return _correlation_id.get()
    return ""


def set_correlation_id(cid: str) -> None:
    if _correlation_id:
        _correlation_id.set(cid)


def get_workflow_id() -> str:
    if _workflow_id:
        return _workflow_id.get()
    return ""


def set_workflow_id(wfid: str) -> None:
    if _workflow_id:
        _workflow_id.set(wfid)


def get_agent_id() -> str:
    if _agent_id:
        return _agent_id.get()
    return ""


def set_agent_id(aid: str) -> None:
    if _agent_id:
        _agent_id.set(aid)


def sanitize_value(key: str, value: str) -> str:
    for pattern in SENSITIVE_FIELD_PATTERNS:
        if pattern.search(key):
            return "***REDACTED***"
    return value


def sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    return {k: ("***REDACTED***" if k.lower() in SANITIZE_HEADERS else v) for k, v in headers.items()}


class JSONLogFormatter(logging.Formatter):
    """Formats log records as JSON objects for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        cid = get_correlation_id()
        if cid:
            log_entry["correlation_id"] = cid

        wfid = get_workflow_id()
        if wfid:
            log_entry["workflow_id"] = wfid

        aid = get_agent_id()
        if aid:
            log_entry["agent_id"] = aid

        rpath = _request_path.get() if _request_path else ""
        if rpath:
            log_entry["request_path"] = rpath

        rmethod = _request_method.get() if _request_method else ""
        if rmethod:
            log_entry["request_method"] = rmethod

        if hasattr(record, "extra_fields"):
            extra = record.extra_fields
            if isinstance(extra, dict):
                log_entry.update(extra)

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]) if record.exc_info[1] else "",
            }

        return json.dumps(log_entry, default=str)


def setup_json_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONLogFormatter())
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(handler)

    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.handlers.clear()
    uvicorn_error.addHandler(handler)

    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.addHandler(handler)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that injects correlation IDs and logs request/response."""

    def __init__(self, app: ASGIApp, exclude_paths: set[str] | None = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or {"/api/health", "/api/v1/health"}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        set_correlation_id(cid)

        rpath = str(request.url.path)
        rmethod = str(request.method)
        if _request_path:
            _request_path.set(rpath)
        if _request_method:
            _request_method.set(rmethod)

        logger = logging.getLogger("openpaper.http")

        if rpath not in self.exclude_paths:
            headers = dict(request.headers)
            safe_headers = sanitize_headers(headers)
            logger.info(
                "Incoming request",
                extra={
                    "extra_fields": {
                        "method": rmethod,
                        "path": rpath,
                        "query": str(request.url.query),
                        "client_host": request.client.host if request.client else "",
                        "headers": safe_headers,
                    }
                },
            )

        start = datetime.now(UTC)
        try:
            response = await call_next(request)
            elapsed = (datetime.now(UTC) - start).total_seconds()

            response.headers["X-Correlation-ID"] = cid

            if rpath not in self.exclude_paths:
                logger.info(
                    "Request completed",
                    extra={
                        "extra_fields": {
                            "method": rmethod,
                            "path": rpath,
                            "status_code": response.status_code,
                            "elapsed_seconds": round(elapsed, 4),
                        }
                    },
                )

            return response
        except Exception as exc:
            elapsed = (datetime.now(UTC) - start).total_seconds()
            logger.error(
                "Request failed",
                extra={
                    "extra_fields": {
                        "method": rmethod,
                        "path": rpath,
                        "elapsed_seconds": round(elapsed, 4),
                        "error": str(exc),
                    }
                },
                exc_info=True,
            )
            raise


class AgentTracingAdapter(logging.LoggerAdapter):
    """Adapter that injects workflow_id and agent_id into all log calls."""

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        extra = kwargs.get("extra", {})
        fields = extra.get("extra_fields", {})
        if isinstance(fields, dict):
            wfid = get_workflow_id()
            if wfid and "workflow_id" not in fields:
                fields["workflow_id"] = wfid
            aid = get_agent_id()
            if aid and "agent_id" not in fields:
                fields["agent_id"] = aid
            extra["extra_fields"] = fields
            kwargs["extra"] = extra
        return msg, kwargs
