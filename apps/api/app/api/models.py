from fastapi import APIRouter

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
async def get_models():
    from app.providers import get_providers
    providers = get_providers()
    result = {}
    for name, provider in providers.items():
        models = await provider.list_models()
        result[name] = models
    return result
