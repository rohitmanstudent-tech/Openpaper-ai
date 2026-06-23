from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.qdrant import init_qdrant
from app.redis import close_redis
from app.plugins.registry import PluginManager
from app.bus.bus import AgentBus
from app.api.v1 import router as api_router
from app.providers.registry import ProviderManager

settings = get_settings()

_plugin_manager: PluginManager | None = None
_agent_bus: AgentBus | None = None
_provider_manager: ProviderManager | None = None


def get_plugin_manager() -> PluginManager:
    global _plugin_manager
    return _plugin_manager


def get_agent_bus() -> AgentBus | None:
    global _agent_bus
    return _agent_bus


def get_provider_manager() -> ProviderManager | None:
    global _provider_manager
    return _provider_manager


async def _init_all_providers(pm: ProviderManager) -> None:
    from app.providers.base import ProviderAuth

    if settings.OLLAMA_BASE_URL:
        from app.providers.ollama_provider import OllamaProvider
        ollama = OllamaProvider(config=ProviderAuth(base_url=settings.OLLAMA_BASE_URL))
        pm.register_provider("ollama", ollama)
        pm.register_model_map("llama3.1", "ollama")
        pm.register_model_map("llama3", "ollama")
        pm.register_model_map("mistral", "ollama")
        pm.register_model_map("mixtral", "ollama")
        pm.register_model_map("codellama", "ollama")
        pm.register_model_map("phi", "ollama")

    if settings.OPENAI_API_KEY:
        from app.providers.openai_provider import OpenAIProvider
        openai = OpenAIProvider(config=ProviderAuth(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL))
        pm.register_provider("openai", openai)
        pm.register_model_map("gpt-4o", "openai")
        pm.register_model_map("gpt-4o-mini", "openai")
        pm.register_model_map("gpt-4", "openai")
        pm.register_model_map("gpt-3.5-turbo", "openai")

    if settings.ANTHROPIC_API_KEY:
        from app.providers.claude_provider import ClaudeProvider
        claude = ClaudeProvider(config=ProviderAuth(api_key=settings.ANTHROPIC_API_KEY, base_url=settings.ANTHROPIC_BASE_URL))
        pm.register_provider("claude", claude)
        pm.register_model_map("claude-3-5-sonnet", "claude")
        pm.register_model_map("claude-3-haiku", "claude")
        pm.register_model_map("claude-3-opus", "claude")

    if settings.GOOGLE_API_KEY:
        from app.providers.gemini_provider import GeminiProvider
        gemini = GeminiProvider(config=ProviderAuth(api_key=settings.GOOGLE_API_KEY, base_url=settings.GEMINI_BASE_URL))
        pm.register_provider("gemini", gemini)
        pm.register_model_map("gemini-1.5-pro", "gemini")
        pm.register_model_map("gemini-1.5-flash", "gemini")

    if settings.XAI_API_KEY:
        from app.providers.grok_provider import GrokProvider
        grok = GrokProvider(config=ProviderAuth(api_key=settings.XAI_API_KEY, base_url=settings.XAI_BASE_URL))
        pm.register_provider("grok", grok)
        pm.register_model_map("grok-2", "grok")
        pm.register_model_map("grok-2-mini", "grok")

    if settings.DEEPSEEK_API_KEY:
        from app.providers.deepseek_provider import DeepSeekProvider
        deepseek = DeepSeekProvider(config=ProviderAuth(api_key=settings.DEEPSEEK_API_KEY, base_url=settings.DEEPSEEK_BASE_URL))
        pm.register_provider("deepseek", deepseek)
        pm.register_model_map("deepseek-chat", "deepseek")
        pm.register_model_map("deepseek-coder", "deepseek")

    if settings.OPENROUTER_API_KEY:
        from app.providers.openrouter_provider import OpenRouterProvider
        openrouter = OpenRouterProvider(config=ProviderAuth(api_key=settings.OPENROUTER_API_KEY, base_url=settings.OPENROUTER_BASE_URL))
        pm.register_provider("openrouter", openrouter)

    if settings.NVIDIA_API_KEY:
        from app.providers.nvidia_provider import NVIDIAProvider
        nvidia = NVIDIAProvider(config=ProviderAuth(api_key=settings.NVIDIA_API_KEY, base_url=settings.NVIDIA_BASE_URL))
        pm.register_provider("nvidia", nvidia)
        pm.register_model_map("nvidia/llama-3.1-nvlm", "nvidia")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _plugin_manager, _agent_bus, _provider_manager

    await init_db()
    try:
        await init_qdrant()
    except Exception:
        pass

    _plugin_manager = PluginManager()
    _plugin_manager.discover(settings.PLUGINS_DIR)
    await _plugin_manager.startup(app=app)

    _provider_manager = ProviderManager(plugin_manager=_plugin_manager)
    await _init_all_providers(_provider_manager)

    from app.redis import redis_client
    _agent_bus = AgentBus(redis=redis_client, plugin_manager=_plugin_manager)

    app.state.plugin_manager = _plugin_manager
    app.state.agent_bus = _agent_bus
    app.state.provider_manager = _provider_manager

    yield

    await _plugin_manager.shutdown(app=app)
    if _agent_bus:
        await _agent_bus.close()
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
