import asyncio

import numpy as np

from ..session.store import EmbeddingStore
from .predictor import (
    BoxPrompt,
    EmbeddingMissing,
    PointPrompt,
    PredictMode,
    PredictResult,
)
from .registry import FAKE_MODEL_NAME, known_models


class FakePredictor:
    """Implémentation mock — génère des masques géométriques.

    - mode="auto"   : ellipse centrale (40% de l'image)
    - mode="box"    : rectangle plein
    - mode="points" : disque rayon = min(h,w)/6 sur le 1er point positif,
                      moins des disques rayon = min(h,w)/12 sur chaque point négatif
    """

    def __init__(self, store: EmbeddingStore) -> None:
        self._store = store
        self._active_model = FAKE_MODEL_NAME
        self._model_lock = asyncio.Lock()

    @property
    def active_model_name(self) -> str:
        return self._active_model

    @property
    def available_models(self) -> list[str]:
        return [FAKE_MODEL_NAME, *known_models()]

    async def load_model(self, name: str) -> None:
        if name not in self.available_models:
            raise ValueError(f"Unknown model: {name}")
        async with self._model_lock:
            self._active_model = name
            await self._store.clear()

    async def set_image(self, session_id: str, image: np.ndarray) -> None:
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(f"image doit être H×W×3, reçu {image.shape}")
        await self._store.put(session_id, image)

    async def predict(
        self,
        session_id: str,
        mode: PredictMode,
        points: list[PointPrompt] | None = None,
        box: BoxPrompt | None = None,
    ) -> PredictResult:
        image = await self._store.get(session_id)
        if image is None:
            raise EmbeddingMissing(session_id)
        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        yy, xx = np.ogrid[:h, :w]

        if mode == "auto":
            cy, cx = h // 2, w // 2
            ry, rx = h * 0.4, w * 0.4
            mask[((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1.0] = 1

        elif mode == "box":
            if box is None:
                raise ValueError("mode=box nécessite un BoxPrompt")
            x1, x2 = sorted((box.x1, box.x2))
            y1, y2 = sorted((box.y1, box.y2))
            x1 = max(0, min(w, x1)); x2 = max(0, min(w, x2))
            y1 = max(0, min(h, y1)); y2 = max(0, min(h, y2))
            mask[y1:y2, x1:x2] = 1

        elif mode == "points":
            if not points:
                raise ValueError("mode=points nécessite au moins un PointPrompt")
            pos_points = [p for p in points if p.label == 1]
            neg_points = [p for p in points if p.label == 0]
            if not pos_points:
                # convention SAM : sans positif, on retourne mask vide
                return PredictResult(mask=mask, score=0.0)
            base_r = min(h, w) // 6
            for p in pos_points:
                mask[(yy - p.y) ** 2 + (xx - p.x) ** 2 <= base_r ** 2] = 1
            neg_r = min(h, w) // 12
            for p in neg_points:
                mask[(yy - p.y) ** 2 + (xx - p.x) ** 2 <= neg_r ** 2] = 0
        else:
            raise ValueError(f"mode inconnu: {mode}")

        return PredictResult(mask=mask, score=0.95)

    async def evict_session(self, session_id: str) -> None:
        await self._store.evict(session_id)

    async def invalidate_all(self) -> None:
        await self._store.clear()

    async def has_embedding(self, session_id: str) -> bool:
        return await self._store.has(session_id)

    async def warmup(self) -> None:
        return None
