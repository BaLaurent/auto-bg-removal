"""Sélection du sujet principal parmi les masks renvoyés par SAM2AutomaticMaskGenerator.

`SAM2AutomaticMaskGenerator.generate(image)` retourne typiquement 30-100 dicts avec :
- `segmentation` : np.ndarray bool H×W
- `area` : int (pixels)
- `predicted_iou` : float
- `point_coords` : list[list[float]]
- `stability_score` : float
- `bbox` : [x, y, w, h]

On veut LE mask qui correspond au sujet principal de l'image (pas le background).
Heuristique : exclure les masks couvrant presque toute l'image (background) ou
quasi rien (bruit), puis maximiser `area × (1 - dist_centroid_au_centre / diag)`.
"""
from typing import Any

import numpy as np

# Ratios de surface relative à exclure
_MAX_RATIO = 0.85  # > 85% de l'image = background plein cadre
_MIN_RATIO = 0.005  # < 0.5% = bruit / artefacts


def select_main_mask(masks: list[dict[str, Any]], image_h: int, image_w: int) -> np.ndarray:
    """Retourne le mask le plus probable du sujet principal en uint8 H×W (0/1).

    Si aucun candidat valide, retourne le mask le plus grand (fallback) ou un
    array vide si la liste est vide.
    """
    if not masks:
        return np.zeros((image_h, image_w), dtype=np.uint8)

    image_area = image_h * image_w
    cx, cy = image_w / 2.0, image_h / 2.0
    diag = float(np.hypot(image_w, image_h))

    scored: list[tuple[float, np.ndarray]] = []
    for m in masks:
        seg = m["segmentation"]
        area = int(m.get("area", int(seg.sum())))
        ratio = area / image_area
        if ratio > _MAX_RATIO or ratio < _MIN_RATIO:
            continue
        ys, xs = np.where(seg)
        if xs.size == 0:
            continue
        mcx = float(xs.mean())
        mcy = float(ys.mean())
        dist = float(np.hypot(mcx - cx, mcy - cy))
        # score normalisé : un mask 2× plus grand bat un mask 1.5× plus central
        score = area * (1.0 - dist / diag)
        scored.append((score, seg.astype(np.uint8)))

    if not scored:
        # fallback : on relâche le seuil de surface (exclut juste le full bg)
        # et on prend le plus grand mask restant.
        non_full_bg = [m for m in masks if m.get("area", 0) / image_area < 0.99]
        if not non_full_bg:
            return np.zeros((image_h, image_w), dtype=np.uint8)
        chosen = max(non_full_bg, key=lambda m: m.get("area", 0))
        return chosen["segmentation"].astype(np.uint8)

    scored.sort(key=lambda c: -c[0])
    return scored[0][1]
