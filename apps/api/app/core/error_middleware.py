"""Request tracing and structured error middleware."""

import sys
import traceback
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AppError

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request/response."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class ExceptionMiddleware(BaseHTTPMiddleware):
    """Catches AppError subclasses and returns structured JSON responses.

    Registered as middleware (instead of app.add_exception_handler) to ensure
    exceptions from dependencies are also caught.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        try:
            return await call_next(request)
        except AppError as exc:
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "error_code": exc.error_code,
                    "message": exc.message,
                    "request_id": request_id,
                    "details": exc.details,
                },
            )
        except Exception:
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            traceback.print_exc(file=sys.stderr)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error_code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                },
            )


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Kept for backward compatibility — delegates to ExceptionMiddleware logic."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    if isinstance(exc, AppError):
        return JSONResponse(status_code=exc.status_code, content={...})
    traceback.print_exc(file=sys.stderr)
    return JSONResponse(status_code=500, content={"success": False, "error_code": "INTERNAL_ERROR", "message": "An unexpected error occurred", "request_id": request_id})
