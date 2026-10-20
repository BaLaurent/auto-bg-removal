from dataclasses import dataclass
from typing import Literal, Protocol

import numpy as np

PredictMode = Literal["points", "box", "auto"]


@dataclass(frozen=True)
class PointPrompt:
    x: int
    y: int
    label: int  # 1 = inclure (positif), 0 = exclure (négatif) — convention SAM 2


@dataclass(frozen=True)
class BoxPrompt:
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass(frozen=True)
class PredictResult:
    mask: np.ndarray  # H×W uint8 (0/1)
    score: float


class EmbeddingMissing(Exception):
    """Levée quand on tente predict sur une session sans embedding (évincée du LRU)."""


class ModelLoading(Exception):
    """Levée quand un appel arrive pendant un swap de modèle."""


class Predictor(Protocol):
    """Interface unifiée — frontière externe avec le moteur ML.

    Implémentations : FakePredictor (mock géométrique), SAM2Predictor (Meta SAM 2).
    """

    @property
    def active_model_name(self) -> str: ...

    @property
    def available_models(self) -> list[str]: ...

    async def load_model(self, name: str) -> None: ...

    async def set_image(self, session_id: str, image: np.ndarray) -> None: ...

    async def predict(
        self,
        session_id: str,
        mode: PredictMode,
        points: list[PointPrompt] | None = None,
        box: BoxPrompt | None = None,
    ) -> PredictResult: ...

    async def evict_session(self, session_id: str) -> None: ...

    async def invalidate_all(self) -> None: ...

    async def has_embedding(self, session_id: str) -> bool: ...

    async def warmup(self) -> None:
        """Précharge ce qui doit être prêt avant le 1er appel HTTP. No-op autorisé."""
