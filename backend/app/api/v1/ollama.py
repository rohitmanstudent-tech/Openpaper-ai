from fastapi import APIRouter, Depends
from app.api.deps import get_provider_manager
from app.core.security import get_current_user
from app.models.user import User
from app.providers.registry import ProviderManager
from app.providers.base import BaseProvider

router = APIRouter()


@router.get("/models")
async def list_ollama_models(
    current_user: User = Depends(get_current_user),
    pm: ProviderManager = Depends(get_provider_manager),
):
    ollama = pm.get_provider("ollama")
    if not ollama:
        return {"models": []}

    try:
        models = await ollama.list_models()
        return {
            "models": [
                {
                    "name": m.name,
                    "id": m.id,
                    "context_length": m.context_length,
                }
                for m in models
            ]
        }
    except Exception:
        return {"models": []}
