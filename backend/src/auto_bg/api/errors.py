from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..segmentation import EmbeddingMissing, ModelLoading


def install(app: FastAPI) -> None:
    @app.exception_handler(EmbeddingMissing)
    async def _embedding_missing(_: Request, exc: EmbeddingMissing) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"error": "embedding_stale", "session_id": str(exc)},
        )

    @app.exception_handler(ModelLoading)
    async def _model_loading(_: Request, __: ModelLoading) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"error": "model_loading"},
        )

    @app.exception_handler(ValueError)
    async def _value_error(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(FileNotFoundError)
    async def _file_not_found(_: Request, exc: FileNotFoundError) -> JSONResponse:
        # Typiquement un checkpoint SAM 2 manquant.
        return JSONResponse(
            status_code=409,
            content={"error": "checkpoint_missing", "detail": str(exc)},
        )

    # Note : torch.OutOfMemoryError n'existe que sur torch>=2.5. On l'identifie
    # par nom pour ne pas dépendre de l'import torch côté API.
    @app.exception_handler(Exception)
    async def _generic(_: Request, exc: Exception) -> JSONResponse:
        name = type(exc).__name__
        if name in ("OutOfMemoryError", "CudaOOMError"):
            return JSONResponse(
                status_code=503,
                content={
                    "error": "gpu_out_of_memory",
                    "detail": "Le GPU n'a pas assez de VRAM pour cette opération. "
                    "Essaye un checkpoint plus petit (tiny/small) ou réduis la taille de l'image.",
                },
            )
        # Tout le reste reste un 500 par défaut FastAPI.
        raise exc
