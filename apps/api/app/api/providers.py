from fastapi import APIRouter

from app.providers import get_providers

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
async def list_providers():
    providers = get_providers()
    result = []
    for name, provider in providers.items():
        health = await provider.check_health()
        models = await provider.list_models()
        result.append(
            {
                "name": name,
                "status": "available" if health else "unavailable",
                "default_model": provider.default_model,
                "model_count": len(models),
            }
        )
    return {"providers": result}


@router.get("/models")
async def list_all_models():
    providers = get_providers()
    result = {}
    for name, provider in providers.items():
        models = await provider.list_models()
        result[name] = models
    return {"models": result}
