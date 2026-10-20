import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import install_error_handlers
from .api import router as api_router
from .config import Settings, get_settings
from .segmentation import FakePredictor, ModelManager, Predictor
from .session import InMemoryLRUStore

logger = logging.getLogger(__name__)


def build_predictor(settings: Settings) -> Predictor:
    store = InMemoryLRUStore(max_size=settings.lru_size)
    if settings.predictor_backend == "fake":
        return FakePredictor(store)
    if settings.predictor_backend == "sam2":
        # imports différés : ne nécessitent pas Torch/SAM 2 pour le mode fake
        from .segmentation.sam2_predictor import SAM2Predictor, async_loader

        manager = ModelManager(
            loader=async_loader,
            model_dir=settings.model_dir,
            initial_model=settings.default_model,
        )
        return SAM2Predictor(store, manager)
    raise ValueError(f"PREDICTOR_BACKEND inconnu: {settings.predictor_backend}")


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        predictor = build_predictor(settings)
        # warmup non-fatal : si le checkpoint manque ou si SAM 2 n'a pas d'autorisation
        # GPU, l'app démarre quand même et expose l'erreur via /api/health.
        # L'utilisateur peut alors télécharger le checkpoint et relancer un predict
        # qui re-déclenchera le load (ensure_loaded est idempotent).
        app.state.warmup_error: str | None = None
        try:
            await predictor.warmup()
        except Exception as exc:  # noqa: BLE001 — on veut tout intercepter ici
            app.state.warmup_error = f"{type(exc).__name__}: {exc}"
            logger.error("Warmup failed (app continues): %s", app.state.warmup_error)
        app.state.predictor = predictor
        app.state.sessions = {}
        app.state.session_images = {}
        yield

    app = FastAPI(title="auto-bg-removal", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_error_handlers(app)
    app.include_router(api_router)

    @app.get("/api/health")
    def health() -> dict[str, object]:
        warmup_err = getattr(app.state, "warmup_error", None)
        return {
            "status": "ok" if warmup_err is None else "degraded",
            "backend": settings.predictor_backend,
            "warmup_error": warmup_err,
        }

    return app


app = create_app()
