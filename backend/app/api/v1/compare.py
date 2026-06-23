from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_provider_manager
from app.core.security import get_current_user
from app.models.user import User
from app.providers.registry import ProviderManager
from app.schemas.provider import CompareRequest, CompareResponse

router = APIRouter()


@router.post("/", response_model=list[CompareResponse])
async def compare_models(
    req: CompareRequest,
    pm: ProviderManager = Depends(get_provider_manager),
    current_user: User = Depends(get_current_user),
):
    if not req.models:
        raise HTTPException(status_code=400, detail="At least one model is required")
    if len(req.models) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 models per comparison")

    results = await pm.compare_models(
        prompt=req.prompt,
        models=req.models,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    return results
