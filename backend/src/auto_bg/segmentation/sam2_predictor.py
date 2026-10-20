"""Wrapper SAM 2 réel.

Pièges connus (à ne pas modifier sans relire) :
- SAM 2 attend du **RGB uint8 H×W×3**, pas du BGR (PIL convient, OpenCV nécessite cvtColor).
- **Pas de normalisation manuelle** : le modèle gère la normalisation interne.
- Coordonnées en **pixels image source** (pas resize). SAM 2 fait le resize en interne.
- `point_labels` : **1 = inclure, 0 = exclure** (pas booléen Python).
- `box=[x1, y1, x2, y2]` xyxy.
- `multimask_output=False` pour un seul mask "le plus probable".
- Forcer **bfloat16** sur GPU compute capability ≥ 8 (Ampere+) pour diviser la VRAM par 2.
- Toutes les opérations PyTorch sont exécutées via `asyncio.to_thread` pour ne pas geler la boucle event.

Cache d'embedding par session :
SAM2ImagePredictor garde l'embedding de l'image courante dans des attributs privés
(`_features`, `_orig_hw`, `_is_image_set`). Pour supporter plusieurs sessions sans
re-faire l'embedding (lent : 0.5-2s GPU) à chaque predict, on snapshot ces attributs
après set_image et on les restaure avant chaque predict. Ces attributs sont privés
donc fragiles : à revérifier à chaque mise à jour de la lib SAM 2.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

import numpy as np

from ..session.store import EmbeddingStore
from . import auto_mask
from .model_manager import ModelManager
from .predictor import (
    BoxPrompt,
    EmbeddingMissing,
    PointPrompt,
    PredictMode,
    PredictResult,
)
from .registry import FAKE_MODEL_NAME, ModelSpec, known_models

if TYPE_CHECKING:
    import torch  # noqa: F401

logger = logging.getLogger(__name__)

# Attributs internes de SAM2ImagePredictor que l'on snapshot/restore.
# Si SAM 2 upgrade casse ces noms, mettre à jour ici.
_SNAPSHOT_ATTRS = ("_features", "_orig_hw", "_is_image_set")


def default_loader(spec: ModelSpec, model_dir: Path) -> Any:
    """Loader par défaut : importe Torch + SAM 2 et construit un SAM2ImagePredictor.

    Synchrone par construction (utilisé via `asyncio.to_thread` côté ModelManager).
    """
    import torch
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    ckpt_path = model_dir / spec.checkpoint
    if not ckpt_path.exists():
        raise FileNotFoundError(
            f"Checkpoint introuvable : {ckpt_path}. "
            f"Lance scripts/download_checkpoints.sh"
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Building SAM 2 (%s) on %s", spec.name, device)

    sam2_model = build_sam2(spec.config_yaml, str(ckpt_path), device=device)
    predictor = SAM2ImagePredictor(sam2_model)
    return predictor


async def async_loader(spec: ModelSpec, model_dir: Path) -> Any:
    """Wrap synchrone → async via thread pool (pour ne pas bloquer la boucle)."""
    return await asyncio.to_thread(default_loader, spec, model_dir)


class SAM2Predictor:
    """Implémentation Predictor sur le vrai SAM 2."""

    def __init__(self, store: EmbeddingStore, manager: ModelManager) -> None:
        self._store = store
        self._mgr = manager
        # Lazy : (id(model_actif), AutomaticMaskGenerator). Reconstruit si le
        # modèle change (load_model invalide via id()).
        self._auto: tuple[int, Any] | None = None

    @property
    def active_model_name(self) -> str:
        return self._mgr.active_name

    @property
    def available_models(self) -> list[str]:
        return [FAKE_MODEL_NAME, *known_models()]

    async def load_model(self, name: str) -> None:
        if name == FAKE_MODEL_NAME:
            raise ValueError("FakePredictor n'est pas chargeable depuis SAM2Predictor")
        await self._mgr.load(name)
        await self._store.clear()
        self._auto = None  # le generator est lié à l'ancien modèle, le re-créer paresseusement

    async def set_image(self, session_id: str, image: np.ndarray) -> None:
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(f"image doit être H×W×3 RGB, reçu {image.shape}")
        _, model = await self._mgr.acquire()
        async with self._mgr.lock:
            snapshot = await asyncio.to_thread(self._set_image_sync, model, image)
        await self._store.put(session_id, snapshot)

    async def predict(
        self,
        session_id: str,
        mode: PredictMode,
        points: list[PointPrompt] | None = None,
        box: BoxPrompt | None = None,
    ) -> PredictResult:
        snapshot = await self._store.get(session_id)
        if snapshot is None:
            raise EmbeddingMissing(session_id)
        _, model = await self._mgr.acquire()
        async with self._mgr.lock:
            return await asyncio.to_thread(
                self._predict_sync, model, snapshot, mode, points, box
            )

    async def evict_session(self, session_id: str) -> None:
        await self._store.evict(session_id)

    async def invalidate_all(self) -> None:
        await self._store.clear()

    async def has_embedding(self, session_id: str) -> bool:
        return await self._store.has(session_id)

    async def warmup(self) -> None:
        await self._mgr.ensure_loaded()

    # ------------------------------------------------------------------
    # implementations synchrones (exécutées dans un thread via to_thread)

    def _set_image_sync(self, model: Any, image: np.ndarray) -> dict[str, Any]:
        import torch

        device = next(model.model.parameters()).device
        ctx = (
            torch.autocast(device_type=device.type, dtype=torch.bfloat16)
            if device.type == "cuda"
            else _NullCtx()
        )
        with torch.inference_mode(), ctx:
            model.set_image(image)
        snap = {k: getattr(model, k) for k in _SNAPSHOT_ATTRS}
        # On stocke aussi l'image source pour le mode "auto" (AutomaticMaskGenerator
        # fait son propre forward et a besoin de l'image, pas de l'embedding caché).
        snap["_source_image"] = image
        return snap

    def _predict_sync(
        self,
        model: Any,
        snapshot: dict[str, Any],
        mode: PredictMode,
        points: list[PointPrompt] | None,
        box: BoxPrompt | None,
    ) -> PredictResult:
        import torch

        if mode == "auto":
            # AutomaticMaskGenerator a besoin de l'image source (pas de l'embedding
            # caché — il fait son propre set_image en interne).
            image = snapshot.get("_source_image")
            if image is None:
                raise ValueError("source image absente du snapshot (incompatible)")
            return self._predict_auto_sync(model, image)

        # Modes points / box : on restaure le state du predictor pour CETTE session
        for k in _SNAPSHOT_ATTRS:
            if k in snapshot:
                setattr(model, k, snapshot[k])

        point_coords = None
        point_labels = None
        box_arr = None

        if mode == "box":
            if box is None:
                raise ValueError("mode=box nécessite un BoxPrompt")
            x1, x2 = sorted((box.x1, box.x2))
            y1, y2 = sorted((box.y1, box.y2))
            box_arr = np.array([x1, y1, x2, y2], dtype=np.float32)
        elif mode == "points":
            if not points:
                raise ValueError("mode=points nécessite au moins un PointPrompt")
            point_coords = np.array([[p.x, p.y] for p in points], dtype=np.float32)
            point_labels = np.array([p.label for p in points], dtype=np.int32)
        else:
            raise ValueError(f"mode inconnu: {mode}")

        device = next(model.model.parameters()).device
        ctx = (
            torch.autocast(device_type=device.type, dtype=torch.bfloat16)
            if device.type == "cuda"
            else _NullCtx()
        )
        with torch.inference_mode(), ctx:
            masks, scores, _ = model.predict(
                point_coords=point_coords,
                point_labels=point_labels,
                box=box_arr,
                multimask_output=False,
            )
        # masks: (1, H, W) bool/uint8 ; scores: (1,)
        return PredictResult(
            mask=np.asarray(masks[0], dtype=np.uint8),
            score=float(scores[0]),
        )

    def _predict_auto_sync(self, model: Any, image: np.ndarray) -> PredictResult:
        """Vrai mode auto : SAM2AutomaticMaskGenerator + heuristique de sélection."""
        import torch
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator

        # Lazy init du generator. Lié à l'identité de l'objet model (qui est
        # le SAM2ImagePredictor : son `.model` est le SAM2Base attendu par le
        # generator). Reconstruit au prochain appel si load_model l'a invalidé.
        #
        # Defaults Meta = 32 points/side + crop_n_layers=1 → ~9 GB VRAM.
        # On baisse pour tenir sur 8 GB ; qualité légèrement moindre mais
        # encore très bonne pour le « sujet principal ».
        if self._auto is None or self._auto[0] != id(model):
            self._auto = (
                id(model),
                SAM2AutomaticMaskGenerator(
                    model.model,
                    points_per_side=16,
                    points_per_batch=16,
                    crop_n_layers=0,
                ),
            )
        generator = self._auto[1]

        device = next(model.model.parameters()).device
        ctx = (
            torch.autocast(device_type=device.type, dtype=torch.bfloat16)
            if device.type == "cuda"
            else _NullCtx()
        )
        with torch.inference_mode(), ctx:
            masks = generator.generate(image)

        h, w = image.shape[:2]
        mask = auto_mask.select_main_mask(masks, h, w)
        # score = predicted_iou du mask sélectionné si on peut le retrouver, sinon 1.0
        chosen_iou = 1.0
        for m in masks:
            if np.array_equal(m["segmentation"].astype(np.uint8), mask):
                chosen_iou = float(m.get("predicted_iou", 1.0))
                break
        return PredictResult(mask=mask, score=chosen_iou)


class _NullCtx:
    def __enter__(self) -> "_NullCtx":
        return self

    def __exit__(self, *_: Any) -> None:
        return None
