import numpy as np
import pytest

from auto_bg.imaging import compose_rgba


def test_alpha_follows_mask():
    img = np.full((10, 10, 3), 100, dtype=np.uint8)
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[3:7, 3:7] = 1
    rgba = compose_rgba(img, mask)
    assert rgba.shape == (10, 10, 4)
    assert rgba.dtype == np.uint8
    assert rgba[5, 5, 3] == 255  # alpha sur mask
    assert rgba[0, 0, 3] == 0  # alpha hors mask
    np.testing.assert_array_equal(rgba[..., :3], img)


def test_mask_shape_mismatch_raises():
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    bad_mask = np.zeros((9, 10), dtype=np.uint8)
    with pytest.raises(ValueError):
        compose_rgba(img, bad_mask)


def test_image_must_be_rgb():
    bad = np.zeros((10, 10, 4), dtype=np.uint8)
    with pytest.raises(ValueError):
        compose_rgba(bad, np.zeros((10, 10), dtype=np.uint8))
