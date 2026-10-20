import numpy as np


def compose_rgba(image_rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Compose une image RGB et un mask binaire en RGBA (alpha = mask × 255)."""
    if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
        raise ValueError(f"image_rgb doit être H×W×3, reçu {image_rgb.shape}")
    if mask.shape != image_rgb.shape[:2]:
        raise ValueError(
            f"mask {mask.shape} incompatible avec image {image_rgb.shape[:2]}"
        )
    alpha = (mask.astype(np.uint8) > 0).astype(np.uint8) * 255
    rgba = np.empty((*image_rgb.shape[:2], 4), dtype=np.uint8)
    rgba[..., :3] = image_rgb
    rgba[..., 3] = alpha
    return rgba
