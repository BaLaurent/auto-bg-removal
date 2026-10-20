from fastapi import APIRouter, Depends

from ..segmentation import FAKE_MODEL_NAME, REGISTRY, Predictor
from .deps import get_predictor
from .schemas import ModelInfo, ModelsResponse, SetActiveRequest

router = APIRouter(tags=["models"])


@router.get("/models", response_model=ModelsResponse)
async def list_models(predictor: Predictor = Depends(get_predictor)) -> ModelsResponse:
    active = predictor.active_model_name
    available: list[ModelInfo] = []
    if FAKE_MODEL_NAME in predictor.available_models:
        available.append(ModelInfo(name=FAKE_MODEL_NAME, loaded=(active == FAKE_MODEL_NAME)))
    for spec in REGISTRY.values():
        available.append(ModelInfo(name=spec.name, loaded=(active == spec.name), size_mb=spec.size_mb))
    return ModelsResponse(active=active, available=available)


@router.post("/models/active", response_model=ModelsResponse)
async def set_active(
    body: SetActiveRequest,
    predictor: Predictor = Depends(get_predictor),
) -> ModelsResponse:
    await predictor.load_model(body.name)
    return await list_models(predictor)
