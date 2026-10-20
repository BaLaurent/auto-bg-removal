import io as _io

import numpy as np
from PIL import Image


def decode_upload(raw: bytes) -> np.ndarray:
    """Décode un upload (bytes) en numpy uint8 H×W×3 RGB.

    SAM 2 attend du RGB pas du BGR : on passe par PIL qui retourne directement RGB.
    Pas de normalisation manuelle (le modèle s'en charge en interne).
    """
    img = Image.open(_io.BytesIO(raw))
    img = img.convert("RGB")
    return np.asarray(img, dtype=np.uint8)


def encode_png(rgba: np.ndarray) -> bytes:
    """Encode un tableau H×W×4 uint8 RGBA en PNG."""
    if rgba.ndim != 3 or rgba.shape[2] != 4 or rgba.dtype != np.uint8:
        raise ValueError("encode_png attend un H×W×4 uint8")
    img = Image.fromarray(rgba, mode="RGBA")
    buf = _io.BytesIO()
    img.save(buf, format="PNG", optimize=False, compress_level=6)
    return buf.getvalue()
