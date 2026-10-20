import asyncio
from pathlib import Path
from typing import Any

import pytest

from auto_bg.segmentation import ModelLoading, ModelManager
from auto_bg.segmentation.registry import ModelSpec


def fake_spec(name: str) -> ModelSpec:
    return ModelSpec(
        name=name,
        config_yaml=f"configs/{name}.yaml",
        checkpoint=f"{name}.pt",
        download_url="",
        size_mb=0,
    )


async def fake_loader(spec: ModelSpec, _model_dir: Path) -> dict[str, Any]:
    return {"name": spec.name, "loaded": True}


async def slow_loader(spec: ModelSpec, _model_dir: Path) -> dict[str, Any]:
    await asyncio.sleep(0.05)
    return {"name": spec.name}


async def test_initial_state():
    mgr = ModelManager(fake_loader, Path("/tmp"), "sam2_hiera_tiny")
    assert mgr.active_name == "sam2_hiera_tiny"
    assert not mgr.is_loading


async def test_load_and_acquire():
    mgr = ModelManager(fake_loader, Path("/tmp"), "sam2_hiera_tiny")
    name, model = await mgr.acquire()
    assert name == "sam2_hiera_tiny"
    assert model["loaded"] is True


async def test_swap_replaces_active():
    mgr = ModelManager(fake_loader, Path("/tmp"), "sam2_hiera_tiny")
    await mgr.ensure_loaded()
    await mgr.load("sam2_hiera_large")
    name, model = await mgr.acquire()
    assert name == "sam2_hiera_large"
    assert model["name"] == "sam2_hiera_large"


async def test_load_unknown_raises():
    mgr = ModelManager(fake_loader, Path("/tmp"), "sam2_hiera_tiny")
    with pytest.raises(ValueError):
        await mgr.load("not_a_model")


async def test_acquire_during_load_raises_modelloading():
    started = asyncio.Event()
    release = asyncio.Event()

    async def blocking_loader(spec: ModelSpec, _: Path) -> dict[str, Any]:
        started.set()
        await release.wait()
        return {"name": spec.name}

    mgr = ModelManager(blocking_loader, Path("/tmp"), "sam2_hiera_tiny")
    load_task = asyncio.create_task(mgr.load("sam2_hiera_tiny"))
    await started.wait()
    # le loader est en cours → is_loading=True → acquire devrait lever ModelLoading
    with pytest.raises(ModelLoading):
        await mgr.acquire()
    release.set()
    await load_task
    name, _ = await mgr.acquire()
    assert name == "sam2_hiera_tiny"


async def test_idempotent_load_same_model():
    calls = 0

    async def counting_loader(spec: ModelSpec, _: Path) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return {"name": spec.name}

    mgr = ModelManager(counting_loader, Path("/tmp"), "sam2_hiera_tiny")
    await mgr.load("sam2_hiera_tiny")
    await mgr.load("sam2_hiera_tiny")
    assert calls == 1


async def test_concurrent_predict_serialized_via_lock():
    mgr = ModelManager(slow_loader, Path("/tmp"), "sam2_hiera_tiny")
    await mgr.ensure_loaded()
    order: list[str] = []

    async def use(label: str) -> None:
        async with mgr.lock:
            order.append(f"{label}:start")
            await asyncio.sleep(0.02)
            order.append(f"{label}:end")

    await asyncio.gather(use("a"), use("b"))
    # les deux blocs ne peuvent pas se chevaucher
    assert order in (
        ["a:start", "a:end", "b:start", "b:end"],
        ["b:start", "b:end", "a:start", "a:end"],
    )
