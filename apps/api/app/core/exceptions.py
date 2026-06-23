"""Standard API exception classes with typed error codes.

All exceptions produce a consistent JSON response:
{
    "success": false,
    "error_code": "PROVIDER_TIMEOUT",
    "message": "Human-readable description",
    "request_id": "uuid"
}
"""

from typing import Any


class AppError(Exception):
    """Base application error with standard response fields."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"
    details: dict[str, Any] | None = None

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        if message:
            self.message = message
        if error_code:
            self.error_code = error_code
        if status_code:
            self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class AuthError(AppError):
    status_code = 401
    error_code = "AUTH_FAILED"
    message = "Authentication failed"


class TokenExpiredError(AppError):
    status_code = 401
    error_code = "TOKEN_EXPIRED"
    message = "Access token has expired"


class PermissionDeniedError(AppError):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    message = "Insufficient permissions"


class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"


class ValidationError(AppError):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Request validation failed"


class ConflictError(AppError):
    status_code = 409
    error_code = "CONFLICT"
    message = "Resource already exists"


class DatabaseError(AppError):
    status_code = 503
    error_code = "DATABASE_ERROR"
    message = "Database operation failed"


class ProviderError(AppError):
    status_code = 502
    error_code = "PROVIDER_ERROR"
    message = "AI provider request failed"


class ProviderTimeoutError(AppError):
    status_code = 504
    error_code = "PROVIDER_TIMEOUT"
    message = "AI provider request timed out"


class ProviderUnavailableError(AppError):
    status_code = 503
    error_code = "PROVIDER_UNAVAILABLE"
    message = "AI provider is not available"


class ProviderAuthError(AppError):
    status_code = 401
    error_code = "PROVIDER_AUTH_FAILED"
    message = "AI provider authentication failed. Check API key"


class AgentError(AppError):
    status_code = 500
    error_code = "AGENT_ERROR"
    message = "Agent execution failed"


class AgentNotFoundError(AppError):
    status_code = 404
    error_code = "AGENT_NOT_FOUND"
    message = "Agent not found"


class OllamaError(AppError):
    status_code = 502
    error_code = "OLLAMA_ERROR"
    message = "Ollama request failed. Is Ollama running?"


class RateLimitError(AppError):
    status_code = 429
    error_code = "RATE_LIMITED"
    message = "Too many requests. Please try again later"
