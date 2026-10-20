import numpy as np

from auto_bg.segmentation.auto_mask import select_main_mask


def _disk_mask(h: int, w: int, cy: int, cx: int, r: int) -> np.ndarray:
    yy, xx = np.ogrid[:h, :w]
    return (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r


def _box_mask(h: int, w: int, y0: int, x0: int, y1: int, x1: int) -> np.ndarray:
    m = np.zeros((h, w), dtype=bool)
    m[y0:y1, x0:x1] = True
    return m


def _entry(seg: np.ndarray, predicted_iou: float = 0.9) -> dict:
    return {"segmentation": seg, "area": int(seg.sum()), "predicted_iou": predicted_iou}


def test_empty_returns_zeros():
    out = select_main_mask([], 10, 10)
    assert out.shape == (10, 10)
    assert out.sum() == 0


def test_picks_central_candidate_over_offcenter():
    h, w = 200, 200
    central = _disk_mask(h, w, 100, 100, 30)  # area ~2826
    corner = _disk_mask(h, w, 30, 30, 30)
    out = select_main_mask([_entry(corner), _entry(central)], h, w)
    np.testing.assert_array_equal(out, central.astype(np.uint8))


def test_excludes_full_background():
    h, w = 100, 100
    bg = np.ones((h, w), dtype=bool)  # 100% de l'image
    central = _disk_mask(h, w, 50, 50, 15)
    out = select_main_mask([_entry(bg), _entry(central)], h, w)
    np.testing.assert_array_equal(out, central.astype(np.uint8))


def test_excludes_tiny_noise():
    h, w = 100, 100
    noise = _disk_mask(h, w, 50, 50, 1)  # ~5 pixels = 0.05% de l'image
    bigger = _disk_mask(h, w, 30, 30, 15)
    out = select_main_mask([_entry(noise), _entry(bigger)], h, w)
    np.testing.assert_array_equal(out, bigger.astype(np.uint8))


def test_prefers_larger_when_both_central():
    h, w = 200, 200
    small = _disk_mask(h, w, 100, 100, 15)
    large = _disk_mask(h, w, 100, 100, 50)
    out = select_main_mask([_entry(small), _entry(large)], h, w)
    np.testing.assert_array_equal(out, large.astype(np.uint8))


def test_fallback_when_all_excluded_picks_largest_non_bg():
    # Toutes les masks sont soit trop petites soit fullbackground
    h, w = 100, 100
    bg = np.ones((h, w), dtype=bool)
    tiny = _disk_mask(h, w, 50, 50, 1)
    medium = _box_mask(h, w, 0, 0, 90, 90)  # 81% — borderline mais sous 85% donc valide
    out = select_main_mask([_entry(bg), _entry(tiny), _entry(medium)], h, w)
    # medium est le seul candidat valide
    np.testing.assert_array_equal(out, medium.astype(np.uint8))


def test_fallback_only_bg_returns_largest_non_bg_or_anything():
    # Cas dégénéré : seules deux masks, l'une bg complet, l'autre 90% (au-dessus du seuil)
    h, w = 100, 100
    bg = np.ones((h, w), dtype=bool)
    huge = _box_mask(h, w, 0, 0, 95, 95)  # 90.25% > 85%
    out = select_main_mask([_entry(bg), _entry(huge)], h, w)
    # Aucun candidat valide → fallback : non-bg le plus grand
    np.testing.assert_array_equal(out, huge.astype(np.uint8))
