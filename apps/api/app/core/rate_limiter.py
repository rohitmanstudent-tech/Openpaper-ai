"""Rate limiter with in-memory fallback and optional Redis backend.

Supports sliding window counters for per-IP and per-endpoint throttling
with automatic cleanup of expired windows.
"""

import logging
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

settings = get_settings()

MemoryStore = dict[str, list[float]]


class SlidingWindowRateLimiter:
    """Sliding window rate limiter backed by either Redis or in-memory dict."""

    def __init__(self):
        self._memory: MemoryStore = defaultdict(list)
        self._cleanup_interval = 60.0
        self._last_cleanup = time.monotonic()

    def _cleanup_expired(self) -> None:
        now = time.monotonic()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        self._last_cleanup = now
        cutoff = now - 3600
        for key in list(self._memory.keys()):
            self._memory[key] = [t for t in self._memory[key] if t > cutoff]
            if not self._memory[key]:
                del self._memory[key]

    def _get_key(self, request: Request, window: str) -> str:
        client_ip = request.client.host if request.client else "unknown"
        route_path = request.url.path
        return f"rl:{client_ip}:{route_path}:{window}"

    async def check(self, request: Request, max_requests: int, window_seconds: int) -> bool:
        if redis_client is not None:
            return await self._check_redis(request, max_requests, window_seconds)
        return self._check_memory(request, max_requests, window_seconds)

    async def _check_redis(self, request: Request, max_requests: int, window: int) -> bool:
        key = self._get_key(request, str(window))
        now = time.time()
        pipeline = redis_client.pipeline()
        pipeline.zremrangebyscore(key, "-inf", now - window)
        pipeline.zcard(key)
        pipeline.zadd(key, {str(now): now})
        pipeline.expire(key, window * 2)
        _, count, _, _ = await pipeline.execute()
        return count < max_requests

    def _check_memory(self, request: Request, max_requests: int, window: int) -> bool:
        self._cleanup_expired()
        key = self._get_key(request, str(window))
        now = time.monotonic()
        self._memory[key] = [t for t in self._memory[key] if t > now - window]
        if len(self._memory[key]) >= max_requests:
            return False
        self._memory[key].append(now)
        return True


_limiter = SlidingWindowRateLimiter()


async def check_rate_limit(
    request: Request,
    max_requests: int = 60,
    window_seconds: int = 60,
) -> bool:
    return await _limiter.check(request, max_requests, window_seconds)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that applies rate limits per endpoint pattern.

    Configuration via RATE_LIMIT_ENABLED, RATE_LIMIT_DEFAULT env vars.
    """

    def __init__(
        self,
        app,
        default_max: int = 60,
        default_window: int = 60,
        strict_routes: dict[str, tuple[int, int]] | None = None,
    ):
        super().__init__(app)
        self.default_max = default_max
        self.default_window = default_window
        self.strict_routes = strict_routes or {}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        route_path = request.url.path
        max_req, window = self.strict_routes.get(route_path, (self.default_max, self.default_window))

        allowed = await _limiter.check(request, max_requests=max_req, window_seconds=window)
        if not allowed:
            client_host = request.client.host if request.client else "unknown"
            logger.warning("Rate limit exceeded for %s from %s", route_path, client_host)
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error_code": "RATE_LIMITED",
                    "message": "Too many requests. Please try again later.",
                    "request_id": getattr(request.state, "request_id", ""),
                },
                headers={"Retry-After": str(window)},
            )

        return await call_next(request)
