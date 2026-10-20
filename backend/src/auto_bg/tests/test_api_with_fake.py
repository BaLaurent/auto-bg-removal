import io as _io

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from auto_bg.imaging import MaskRLE, decode as decode_mask
from auto_bg.main import create_app


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


def _png_bytes(w: int = 64, h: int = 48) -> bytes:
    arr = np.full((h, w, 3), 200, dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_create_session_then_predict_auto(client):
    r = await client.post(
        "/api/sessions", files={"file": ("img.png", _png_bytes(), "image/png")}
    )
    assert r.status_code == 201, r.text
    sid = r.json()["session_id"]
    assert r.json()["image"] == {"width": 64, "height": 48}

    pr = await client.post(f"/api/sessions/{sid}/predict", json={"mode": "auto"})
    assert pr.status_code == 200, pr.text
    body = pr.json()
    assert body["mask"]["size"] == [48, 64]
    rle = MaskRLE(counts_b64=body["mask"]["counts"], height=48, width=64)
    mask = decode_mask(rle)
    assert mask.shape == (48, 64)
    assert mask.sum() > 0  # ellipse centrale


async def test_predict_box(client):
    sid = (
        await client.post("/api/sessions", files={"file": ("i.png", _png_bytes(), "image/png")})
    ).json()["session_id"]
    pr = await client.post(
        f"/api/sessions/{sid}/predict",
        json={"mode": "box", "box": {"x1": 10, "y1": 5, "x2": 30, "y2": 25}},
    )
    assert pr.status_code == 200
    rle_dto = pr.json()["mask"]
    mask = decode_mask(MaskRLE(counts_b64=rle_dto["counts"], height=rle_dto["size"][0], width=rle_dto["size"][1]))
    assert mask[15, 20] == 1
    assert mask[0, 0] == 0


async def test_predict_points(client):
    sid = (
        await client.post("/api/sessions", files={"file": ("i.png", _png_bytes(128, 128), "image/png")})
    ).json()["session_id"]
    pr = await client.post(
        f"/api/sessions/{sid}/predict",
        json={"mode": "points", "points": [{"x": 64, "y": 64, "label": 1}]},
    )
    assert pr.status_code == 200
    rle_dto = pr.json()["mask"]
    mask = decode_mask(MaskRLE(counts_b64=rle_dto["counts"], height=rle_dto["size"][0], width=rle_dto["size"][1]))
    assert mask[64, 64] == 1


async def test_models_list_and_switch(client):
    r = await client.get("/api/models")
    assert r.status_code == 200
    body = r.json()
    assert body["active"] == "fake_predictor"
    names = [m["name"] for m in body["available"]]
    assert "sam2_hiera_large" in names
    assert "fake_predictor" in names

    r2 = await client.post("/api/models/active", json={"name": "sam2_hiera_tiny"})
    assert r2.status_code == 200
    assert r2.json()["active"] == "sam2_hiera_tiny"


async def test_switch_model_invalidates_session(client):
    sid = (
        await client.post("/api/sessions", files={"file": ("i.png", _png_bytes(), "image/png")})
    ).json()["session_id"]
    await client.post("/api/models/active", json={"name": "sam2_hiera_tiny"})
    pr = await client.post(f"/api/sessions/{sid}/predict", json={"mode": "auto"})
    assert pr.status_code == 409
    assert pr.json()["error"] == "embedding_stale"


async def test_recompute_after_switch(client):
    sid = (
        await client.post("/api/sessions", files={"file": ("i.png", _png_bytes(), "image/png")})
    ).json()["session_id"]
    await client.post("/api/models/active", json={"name": "sam2_hiera_tiny"})
    rc = await client.post(f"/api/sessions/{sid}/recompute")
    assert rc.status_code == 200
    pr = await client.post(f"/api/sessions/{sid}/predict", json={"mode": "auto"})
    assert pr.status_code == 200


async def test_export_returns_png_with_alpha(client):
    sid_resp = await client.post("/api/sessions", files={"file": ("i.png", _png_bytes(64, 48), "image/png")})
    sid = sid_resp.json()["session_id"]
    pr = await client.post(f"/api/sessions/{sid}/predict", json={"mode": "auto"})
    mask_dto = pr.json()["mask"]

    er = await client.post(
        f"/api/sessions/{sid}/export",
        json={"mask": mask_dto},
    )
    assert er.status_code == 200
    assert er.headers["content-type"] == "image/png"
    out = Image.open(_io.BytesIO(er.content))
    assert out.mode == "RGBA"
    assert out.size == (64, 48)
    arr = np.array(out)
    # au moins un pixel transparent et un pixel opaque
    assert (arr[..., 3] == 0).any()
    assert (arr[..., 3] == 255).any()


async def test_delete_session(client):
    sid = (
        await client.post("/api/sessions", files={"file": ("i.png", _png_bytes(), "image/png")})
    ).json()["session_id"]
    r = await client.delete(f"/api/sessions/{sid}")
    assert r.status_code == 204
    state = await client.get(f"/api/sessions/{sid}")
    assert state.status_code == 404


async def test_session_not_found_404(client):
    r = await client.post("/api/sessions/missing/predict", json={"mode": "auto"})
    assert r.status_code == 404
