from fastapi import APIRouter, Depends, Request

from ..imaging import encode as encode_mask
from ..segmentation import (
    BoxPrompt,
    PointPrompt,
    Predictor,
)
from .deps import get_predictor, get_session
from .schemas import MaskRLEDTO, PredictRequest, PredictResponse

router = APIRouter(tags=["predict"])


@router.post("/sessions/{session_id}/predict", response_model=PredictResponse)
async def predict(
    request: Request,
    session_id: str,
    body: PredictRequest,
    predictor: Predictor = Depends(get_predictor),
) -> PredictResponse:
    get_session(request, session_id)  # 404 si inconnu

    points: list[PointPrompt] | None = None
    if body.points:
        points = [PointPrompt(x=p.x, y=p.y, label=p.label) for p in body.points]
    box: BoxPrompt | None = None
    if body.box:
        box = BoxPrompt(x1=body.box.x1, y1=body.box.y1, x2=body.box.x2, y2=body.box.y2)

    result = await predictor.predict(session_id, body.mode, points=points, box=box)
    rle = encode_mask(result.mask)
    return PredictResponse(
        mask=MaskRLEDTO(counts=rle.counts_b64, size=(rle.height, rle.width)),
        score=float(result.score),
        model=predictor.active_model_name,
    )
