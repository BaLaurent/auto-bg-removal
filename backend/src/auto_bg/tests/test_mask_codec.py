import numpy as np

from auto_bg.imaging import decode, encode


def test_roundtrip_random_mask():
    rng = np.random.default_rng(42)
    mask = (rng.random((37, 53)) > 0.7).astype(np.uint8)
    rle = encode(mask)
    back = decode(rle)
    assert back.shape == mask.shape
    np.testing.assert_array_equal(back, mask)


def test_roundtrip_all_zero():
    mask = np.zeros((20, 30), dtype=np.uint8)
    back = decode(encode(mask))
    np.testing.assert_array_equal(back, mask)


def test_roundtrip_all_one():
    mask = np.ones((20, 30), dtype=np.uint8)
    back = decode(encode(mask))
    np.testing.assert_array_equal(back, mask)


def test_encode_2d_only():
    import pytest

    with pytest.raises(ValueError):
        encode(np.zeros((10, 10, 3), dtype=np.uint8))


def test_dimensions_preserved():
    mask = np.zeros((101, 73), dtype=np.uint8)
    rle = encode(mask)
    assert rle.height == 101
    assert rle.width == 73
