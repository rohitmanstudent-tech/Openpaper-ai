"""Sentry integration for production error monitoring."""

import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
_sentry_initialized = False


def init_sentry() -> None:
    """Initialize Sentry SDK if SENTRY_DSN is configured."""
    global _sentry_initialized
    settings = get_settings()

    dsn = getattr(settings, "SENTRY_DSN", None) or ""
    if not dsn:
        logger.info("SENTRY_DSN not set — skipping Sentry initialization")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment="production" if not settings.DEBUG else "development",
            release=settings.VERSION,
            traces_sample_rate=0.2 if not settings.DEBUG else 1.0,
            profiles_sample_rate=0.1,
            integrations=[
                FastApiIntegration(),
                LoggingIntegration(level=logging.WARNING, event_level=logging.ERROR),
                SqlalchemyIntegration(),
            ],
            send_default_pii=False,
        )
        _sentry_initialized = True
        logger.info("Sentry initialized (DSN: %s...)", dsn[:20])
    except ImportError:
        logger.warning("sentry-sdk not installed — skipping Sentry initialization")
    except Exception as e:
        logger.warning("Failed to initialize Sentry: %s", e)


def capture_error(exc: BaseException, request_id: str | None = None) -> None:
    """Manually capture an error to Sentry (for non-request contexts)."""
    if not _sentry_initialized:
        return
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if request_id:
                scope.set_tag("request_id", request_id)
            sentry_sdk.capture_exception(exc)
    except ImportError:
        pass
