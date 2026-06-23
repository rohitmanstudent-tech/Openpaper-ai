"""Startup environment validation.

Raises EnvironmentError with clear instructions on missing or misconfigured
environment variables — fails fast instead of failing mysteriously at runtime.
"""
import sys
from collections.abc import Callable
from dataclasses import dataclass, field

from app.config import get_settings

settings = get_settings()


@dataclass
class ValidationResult:
    passed: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.passed = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        self.passed = self.passed and other.passed
        self.warnings.extend(other.warnings)
        self.errors.extend(other.errors)
        if self.errors:
            self.passed = False
        return self


ValidatorFn = Callable[[], ValidationResult]


def check_secret_key() -> ValidationResult:
    r = ValidationResult()
    if not settings.SECRET_KEY:
        r.add_error("SECRET_KEY is empty — set a random 32+ character string")
    elif settings.SECRET_KEY in (
        "super-secret-key-change-in-production",
        "change-this-to-a-random-secret-key",
        "change-this-in-production",
    ):
        r.add_error(
            "SECRET_KEY is still set to the default value. "
            "Generate a secure random key:\n"
            "  python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    return r


def check_database_url() -> ValidationResult:
    r = ValidationResult()
    url = settings.DATABASE_URL
    if not url:
        r.add_error("DATABASE_URL is not set")
    elif "localhost" in url:
        r.add_warning("DATABASE_URL points to localhost — will not work inside Docker containers")
    return r


def check_redis_url() -> ValidationResult:
    r = ValidationResult()
    if not settings.REDIS_URL:
        r.add_error("REDIS_URL is not set")
    return r


def check_cors_origins() -> ValidationResult:
    r = ValidationResult()
    cors = getattr(settings, "CORS_ORIGINS", None)
    if cors and cors == "*":
        r.add_warning("CORS_ORIGINS is set to '*' — restrict to specific origins in production")
    return r


def check_debug_mode() -> ValidationResult:
    r = ValidationResult()
    if settings.DEBUG:
        r.add_warning("DEBUG=True — disable in production for security and performance")
    return r


def check_providers() -> ValidationResult:
    r = ValidationResult()
    has_openai = bool(settings.OPENAI_API_KEY)
    has_anthropic = bool(settings.ANTHROPIC_API_KEY)
    has_openrouter = bool(settings.OPENROUTER_API_KEY)

    if not any([has_openai, has_anthropic, has_openrouter]):
        r.add_warning(
            "No AI provider API keys configured (OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY). "
            "Ollama will be used as the default provider. Set at least one API key for cloud providers."
        )
    return r


def check_access_token_expiry() -> ValidationResult:
    r = ValidationResult()
    if settings.ACCESS_TOKEN_EXPIRE_MINUTES > 1440:
        r.add_warning(
            f"ACCESS_TOKEN_EXPIRE_MINUTES={settings.ACCESS_TOKEN_EXPIRE_MINUTES} (> 1 day) — "
            "consider a shorter expiry for security"
        )
    return r


VALIDATORS: list[ValidatorFn] = [
    check_secret_key,
    check_database_url,
    check_redis_url,
    check_cors_origins,
    check_debug_mode,
    check_providers,
    check_access_token_expiry,
]


def run_validation(*, exit_on_error: bool = True) -> ValidationResult:
    result = ValidationResult()
    for fn in VALIDATORS:
        try:
            result.merge(fn())
        except Exception as e:
            result.errors.append(f"Validator {fn.__name__} crashed: {e}")

    for w in result.warnings:
        print(f"[WARN]  {w}", file=sys.stderr)

    if result.errors:
        print("\n[FAIL] Environment validation failed:\n", file=sys.stderr)
        for e in result.errors:
            print(f"  ✖  {e}", file=sys.stderr)
        print(file=sys.stderr)
        if exit_on_error:
            sys.exit(1)

    return result
