from fastapi import APIRouter

from . import export, models, predict, sessions
from .errors import install as install_error_handlers

router = APIRouter(prefix="/api")
router.include_router(sessions.router)
router.include_router(predict.router)
router.include_router(models.router)
router.include_router(export.router)

__all__ = ["router", "install_error_handlers"]
