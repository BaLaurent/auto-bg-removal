import io as _io

import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def red_square_png_bytes() -> bytes:
    arr = np.full((128, 128, 3), [220, 40, 40], dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def small_image_rgb() -> np.ndarray:
    return np.full((64, 96, 3), 200, dtype=np.uint8)
