"""Security headers middleware for web security best practices.

Adds CSP, HSTS, X-Frame-Options, X-Content-Type-Options, and other
security-related HTTP headers to every response.
"""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to all responses.

    Headers are configurable via environment variables but ship with
    sensible production defaults.
    """

    def __init__(
        self,
        app,
        csp_default_src: str = "'self'",
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
    ):
        super().__init__(app)
        self._csp = (
            f"default-src {csp_default_src}; "
            f"script-src {csp_default_src} 'unsafe-inline' https://js.stripe.com; "
            f"style-src {csp_default_src} 'unsafe-inline' https://fonts.googleapis.com; "
            f"img-src {csp_default_src} data: blob: https:; "
            f"connect-src {csp_default_src} https://api.stripe.com; "
            f"font-src {csp_default_src} https://fonts.gstatic.com; "
            f"frame-src https://js.stripe.com; "
            f"object-src 'none'; "
            f"base-uri {csp_default_src}; "
            f"form-action {csp_default_src}"
        )
        self._hsts = f"max-age={hsts_max_age}" + ("; includeSubDomains" if hsts_include_subdomains else "")

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = self._hsts
            response.headers["Content-Security-Policy"] = self._csp
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), interest-cohort=()"

        return response
