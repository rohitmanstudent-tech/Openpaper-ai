from app.core.validator import (
    ValidationResult,
    check_database_url,
    check_debug_mode,
    check_providers,
    check_secret_key,
    run_validation,
)


class TestSecretKey:
    def test_empty_key(self):
        from app.config import get_settings

        s = get_settings()
        original = s.SECRET_KEY
        s.SECRET_KEY = ""
        try:
            r = check_secret_key()
            assert not r.passed
            assert any("empty" in e.lower() for e in r.errors)
        finally:
            s.SECRET_KEY = original

    def test_default_key_warns(self):
        s = check_secret_key()
        if s.errors:
            assert any("default" in e.lower() for e in s.errors)


class TestDatabaseUrl:
    def test_localhost_warning(self):
        from app.config import get_settings

        s = get_settings()
        original = s.DATABASE_URL
        s.DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/db"
        try:
            r = check_database_url()
            assert any("localhost" in w.lower() for w in r.warnings)
        finally:
            s.DATABASE_URL = original

    def test_empty_url(self):
        from app.config import get_settings

        s = get_settings()
        original = s.DATABASE_URL
        s.DATABASE_URL = ""
        try:
            r = check_database_url()
            assert not r.passed
        finally:
            s.DATABASE_URL = original


class TestDebugMode:
    def test_debug_warning(self):
        from app.config import get_settings

        s = get_settings()
        original = s.DEBUG
        s.DEBUG = True
        try:
            r = check_debug_mode()
            assert any("DEBUG" in w for w in r.warnings)
        finally:
            s.DEBUG = original


class TestProviders:
    def test_no_keys_warning(self):
        from app.config import get_settings

        s = get_settings()
        orig_openai = s.OPENAI_API_KEY
        orig_anthropic = s.ANTHROPIC_API_KEY
        orig_openrouter = s.OPENROUTER_API_KEY
        s.OPENAI_API_KEY = ""
        s.ANTHROPIC_API_KEY = ""
        s.OPENROUTER_API_KEY = ""
        try:
            r = check_providers()
            assert any("API key" in w for w in r.warnings)
        finally:
            s.OPENAI_API_KEY = orig_openai
            s.ANTHROPIC_API_KEY = orig_anthropic
            s.OPENROUTER_API_KEY = orig_openrouter


class TestRunValidation:
    def test_validation_result_type(self):
        r = run_validation(exit_on_error=False)
        assert isinstance(r, ValidationResult)

    def test_validation_does_not_crash(self):
        r = run_validation(exit_on_error=False)
        assert hasattr(r, "passed")
        assert hasattr(r, "warnings")
        assert hasattr(r, "errors")
