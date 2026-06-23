from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_provider_manager, get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.providers.registry import ProviderManager
from app.schemas.provider import (
    ProviderStatusResponse,
    UsageRecord,
    UsageStatsResponse,
)
from app.services.auth import AuthService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=list[ProviderStatusResponse])
async def list_providers(
    pm: ProviderManager = Depends(get_provider_manager),
    current_user: User = Depends(get_current_user),
):
    return await pm.get_providers_status()


@router.get("/{provider_name}/models")
async def get_provider_models(
    provider_name: str,
    pm: ProviderManager = Depends(get_provider_manager),
    current_user: User = Depends(get_current_user),
):
    prov = pm.get_provider(provider_name)
    if not prov:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    try:
        models = await prov.list_models()
        return {
            "provider": provider_name,
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "context_length": m.context_length,
                    "pricing_input_per_1k": m.pricing_input_per_1k,
                    "pricing_output_per_1k": m.pricing_output_per_1k,
                    "capabilities": m.capabilities,
                }
                for m in models
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch models from '{provider_name}': {str(e)}",
        )


@router.get("/usage/stats", response_model=UsageStatsResponse)
async def get_usage_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.providers.cost_tracker import CostTracker
    tracker = CostTracker(db)
    return await tracker.get_aggregated(user_id=current_user.id)


@router.get("/usage/records", response_model=list[UsageRecord])
async def get_usage_records(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.providers.cost_tracker import CostTracker
    tracker = CostTracker(db)
    records = await tracker.get_usage(user_id=current_user.id, limit=limit)
    return [UsageRecord.model_validate(r) for r in records]
