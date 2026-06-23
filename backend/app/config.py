from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import list


class Settings(BaseSettings):
    APP_NAME: str = "OpenPaper AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://openpaper:openpaper_secret@localhost:5432/openpaper"
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"

    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

    # ─── Ollama (local) ──────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.1"

    # ─── OpenAI ──────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_DEFAULT_MODEL: str = "gpt-4o"

    # ─── Anthropic Claude ────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com/v1"
    ANTHROPIC_DEFAULT_MODEL: str = "claude-3-5-sonnet-20240620"

    # ─── Google Gemini ───────────────────────────────────────────
    GOOGLE_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_DEFAULT_MODEL: str = "gemini-1.5-pro"

    # ─── xAI Grok ────────────────────────────────────────────────
    XAI_API_KEY: str = ""
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    XAI_DEFAULT_MODEL: str = "grok-2"

    # ─── DeepSeek ────────────────────────────────────────────────
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_DEFAULT_MODEL: str = "deepseek-chat"

    # ─── OpenRouter ──────────────────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_DEFAULT_MODEL: str = "openai/gpt-4o"

    # ─── NVIDIA NIM ──────────────────────────────────────────────
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_DEFAULT_MODEL: str = "nvidia/llama-3.1-nvlm-8b"

    # ─── AI Provider Fallback & Routing ──────────────────────────
    AI_FALLBACK_ORDER: list[str] = [
        "openai", "claude", "gemini", "grok",
        "deepseek", "openrouter", "ollama", "nvidia",
    ]
    AI_LOCAL_FIRST: bool = False
    AI_LOCAL_PROVIDERS: list[str] = ["ollama", "nvidia"]
    AI_CLOUD_PROVIDERS: list[str] = [
        "openai", "claude", "gemini", "grok",
        "deepseek", "openrouter",
    ]
    AI_DEFAULT_PROVIDER: str = "ollama"
    AI_DEFAULT_MODEL: str = "llama3.1"

    # ─── Plugin System ─────────────────────────────────────────────
    PLUGINS_DIR: str = "plugins"
    PLUGIN_AUTO_DISCOVER: bool = True

    # ─── Agent Bus ─────────────────────────────────────────────────
    BUS_RESPONSE_TIMEOUT: int = 30
    BUS_MESSAGE_TTL: int = 86400

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
