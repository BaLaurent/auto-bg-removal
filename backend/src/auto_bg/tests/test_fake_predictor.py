import numpy as np
import pytest

from auto_bg.segmentation import (
    BoxPrompt,
    EmbeddingMissing,
    FakePredictor,
    PointPrompt,
)
from auto_bg.session import InMemoryLRUStore


@pytest.fixture
def predictor() -> FakePredictor:
    return FakePredictor(InMemoryLRUStore(max_size=4))


@pytest.fixture
def image() -> np.ndarray:
    return np.zeros((100, 200, 3), dtype=np.uint8)


async def test_predict_without_set_image_raises(predictor):
    with pytest.raises(EmbeddingMissing):
        await predictor.predict("missing", "auto")


async def test_auto_returns_central_ellipse(predictor, image):
    await predictor.set_image("s1", image)
    result = await predictor.predict("s1", "auto")
    h, w = image.shape[:2]
    assert result.mask.shape == (h, w)
    assert result.mask[h // 2, w // 2] == 1
    assert result.mask[0, 0] == 0  # coin loin du centre


async def test_box_paints_rectangle(predictor, image):
    await predictor.set_image("s1", image)
    box = BoxPrompt(x1=10, y1=20, x2=50, y2=60)
    result = await predictor.predict("s1", "box", box=box)
    assert result.mask[40, 30] == 1
    assert result.mask[5, 5] == 0


async def test_box_normalizes_inverted(predictor, image):
    await predictor.set_image("s1", image)
    box = BoxPrompt(x1=50, y1=60, x2=10, y2=20)
    result = await predictor.predict("s1", "box", box=box)
    assert result.mask[40, 30] == 1


async def test_points_positive_creates_disk(predictor, image):
    await predictor.set_image("s1", image)
    p = PointPrompt(x=100, y=50, label=1)
    result = await predictor.predict("s1", "points", points=[p])
    assert result.mask[50, 100] == 1


async def test_points_negative_carves_hole(predictor, image):
    await predictor.set_image("s1", image)
    pos = PointPrompt(x=100, y=50, label=1)
    neg = PointPrompt(x=100, y=50, label=0)  # même endroit
    result = await predictor.predict("s1", "points", points=[pos, neg])
    assert result.mask[50, 100] == 0  # creusé par le négatif


async def test_no_positive_returns_empty(predictor, image):
    await predictor.set_image("s1", image)
    p = PointPrompt(x=10, y=10, label=0)
    result = await predictor.predict("s1", "points", points=[p])
    assert result.mask.sum() == 0
    assert result.score == 0.0


async def test_invalidate_all_clears_embeddings(predictor, image):
    await predictor.set_image("s1", image)
    await predictor.invalidate_all()
    with pytest.raises(EmbeddingMissing):
        await predictor.predict("s1", "auto")


async def test_load_model_clears_cache(predictor, image):
    await predictor.set_image("s1", image)
    await predictor.load_model("sam2_hiera_tiny")
    with pytest.raises(EmbeddingMissing):
        await predictor.predict("s1", "auto")
    assert predictor.active_model_name == "sam2_hiera_tiny"


async def test_load_unknown_model_raises(predictor):
    with pytest.raises(ValueError):
        await predictor.load_model("not_a_model")
