from fastapi import APIRouter, Depends, Query

from app.api.deps import get_provider_manager
from app.core.security import get_current_user
from app.models.user import User
from app.providers.registry import ProviderManager
from app.schemas.provider import ModelInfoResponse

router = APIRouter()


@router.get("/", response_model=list[ModelInfoResponse])
async def list_models(
    provider: str | None = Query(None, description="Filter by provider name"),
    pm: ProviderManager = Depends(get_provider_manager),
    current_user: User = Depends(get_current_user),
):
    all_models = await pm.get_all_models()
    if provider:
        all_models = [m for m in all_models if m["provider"] == provider]
    return all_models
