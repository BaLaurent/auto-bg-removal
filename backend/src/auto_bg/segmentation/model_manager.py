import asyncio
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable

from .predictor import ModelLoading
from .registry import ModelSpec, get_spec

logger = logging.getLogger(__name__)

# Type d'un loader injecté : (spec, model_dir) -> opaque object (le SAM2ImagePredictor en prod)
ModelLoader = Callable[[ModelSpec, Path], Awaitable[Any]]


class ModelManager:
    """Garde en VRAM **une seule** instance de modèle actif.

    Contrats :
    - Le swap de modèle est synchrone côté API (POST /models/active retourne quand le load est fini).
    - Pendant un swap, tout `acquire()` lève `ModelLoading` (HTTP 503).
    - Le loader injecté est responsable de l'init Torch ; le manager ne fait que la coordination.
    """

    def __init__(
        self,
        loader: ModelLoader,
        model_dir: Path,
        initial_model: str,
    ) -> None:
        self._loader = loader
        self._model_dir = model_dir
        self._lock = asyncio.Lock()
        self._loading = False
        self._active_name: str | None = None
        self._active_model: Any | None = None
        self._initial = initial_model

    @property
    def active_name(self) -> str:
        return self._active_name or self._initial

    @property
    def is_loading(self) -> bool:
        return self._loading

    async def ensure_loaded(self) -> Any:
        """Charge le modèle initial si pas déjà fait. Idempotent."""
        if self._active_model is not None:
            return self._active_model
        await self.load(self._initial)
        return self._active_model

    async def load(self, name: str) -> Any:
        """Charge le modèle `name`. Bloque les autres `acquire()` pendant le load.

        Atomicité : si le loader échoue, l'ancien modèle reste actif. Cela double
        brièvement la VRAM pendant le swap, mais évite que l'API se retrouve sans
        aucun modèle utilisable sur erreur (checkpoint manquant, OOM, …).
        """
        spec = get_spec(name)
        if self._loading:
            raise ModelLoading(name)
        async with self._lock:
            if self._active_name == name and self._active_model is not None:
                return self._active_model
            self._loading = True
            try:
                logger.info("Loading SAM 2 model %s from %s", name, self._model_dir)
                model = await self._loader(spec, self._model_dir)
                # Swap atomique : ancien modèle remplacé seulement après succès.
                self._active_model = model
                self._active_name = name
                logger.info("Loaded %s", name)
                return model
            finally:
                self._loading = False

    async def acquire(self) -> tuple[str, Any]:
        """Retourne (nom, modèle) pour usage. Lève ModelLoading si swap en cours."""
        if self._loading:
            raise ModelLoading(self._active_name or "unknown")
        if self._active_model is None:
            await self.ensure_loaded()
        assert self._active_name is not None and self._active_model is not None
        return self._active_name, self._active_model

    @property
    def lock(self) -> asyncio.Lock:
        """Lock partagé pour sérialiser les appels GPU (set_image / predict)."""
        return self._lock
