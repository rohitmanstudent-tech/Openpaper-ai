from fastapi import APIRouter
from app.api.v1 import auth, users, agents, chat, memory, tasks, ollama
from app.api.v1 import models as models_router
from app.api.v1 import providers as providers_router
from app.api.v1 import compare as compare_router
from app.api.v1 import plugins as plugins_router
from app.api.v1 import bus as bus_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(agents.router, prefix="/agents", tags=["Agents"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(memory.router, prefix="/memory", tags=["Memory"])
router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
router.include_router(ollama.router, prefix="/ollama", tags=["Ollama"])

router.include_router(models_router.router, prefix="/models", tags=["AI Models"])
router.include_router(providers_router.router, prefix="/providers", tags=["AI Providers"])
router.include_router(compare_router.router, prefix="/compare", tags=["AI Compare"])
router.include_router(plugins_router.router, prefix="/plugins", tags=["Plugins"])
router.include_router(bus_router.router, prefix="/bus", tags=["Agent Bus"])
