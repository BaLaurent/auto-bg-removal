from fastapi import APIRouter, Depends, File, Request, Response, UploadFile

from ..imaging import decode_upload
from ..segmentation import Predictor
from ..session import ImageMeta, Session
from .deps import get_predictor, get_session, get_session_registry
from .schemas import ImageSize, SessionCreated, SessionState

router = APIRouter(tags=["sessions"])


@router.post("/sessions", status_code=201, response_model=SessionCreated)
async def create_session(
    request: Request,
    file: UploadFile = File(...),
    predictor: Predictor = Depends(get_predictor),
) -> SessionCreated:
    raw = await file.read()
    image = decode_upload(raw)
    h, w = image.shape[:2]
    sess = Session.new(
        image_meta=ImageMeta(width=w, height=h),
        model_name=predictor.active_model_name,
    )
    await predictor.set_image(sess.id, image)
    request.app.state.sessions[sess.id] = sess
    request.app.state.session_images[sess.id] = image
    return SessionCreated(
        session_id=sess.id,
        image=ImageSize(width=w, height=h),
        embedding_ready=True,
        model=sess.model_name,
    )


@router.get("/sessions/{session_id}", response_model=SessionState)
async def get_session_state(
    request: Request,
    session_id: str,
    predictor: Predictor = Depends(get_predictor),
) -> SessionState:
    sess = get_session(request, session_id)
    ready = await predictor.has_embedding(session_id)
    return SessionState(
        session_id=sess.id,
        embedding_ready=ready and sess.model_name == predictor.active_model_name,
        model=predictor.active_model_name,
    )


@router.post("/sessions/{session_id}/recompute", status_code=200)
async def recompute(
    request: Request,
    session_id: str,
    predictor: Predictor = Depends(get_predictor),
) -> SessionState:
    sess = get_session(request, session_id)
    image = request.app.state.session_images.get(session_id)
    if image is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=410, detail="image_unavailable")
    await predictor.set_image(session_id, image)
    sess.model_name = predictor.active_model_name
    return SessionState(
        session_id=sess.id,
        embedding_ready=True,
        model=sess.model_name,
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    request: Request,
    session_id: str,
    predictor: Predictor = Depends(get_predictor),
) -> Response:
    await predictor.evict_session(session_id)
    sessions = get_session_registry(request)
    sessions.pop(session_id, None)
    request.app.state.session_images.pop(session_id, None)
    return Response(status_code=204)
