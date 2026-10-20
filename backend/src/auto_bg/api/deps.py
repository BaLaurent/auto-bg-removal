from fastapi import HTTPException, Request

from ..segmentation import Predictor
from ..session import Session


def get_predictor(request: Request) -> Predictor:
    return request.app.state.predictor


def get_session_registry(request: Request) -> dict[str, Session]:
    return request.app.state.sessions


def get_session(request: Request, session_id: str) -> Session:
    sessions = get_session_registry(request)
    sess = sessions.get(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    return sess
