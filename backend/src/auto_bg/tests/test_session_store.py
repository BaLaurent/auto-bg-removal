import asyncio

import pytest

from auto_bg.session import InMemoryLRUStore


async def test_put_get():
    store = InMemoryLRUStore(max_size=4)
    await store.put("a", 1)
    assert await store.get("a") == 1


async def test_eviction_lru_order():
    store = InMemoryLRUStore(max_size=2)
    await store.put("a", 1)
    await store.put("b", 2)
    await store.put("c", 3)
    assert await store.get("a") is None  # le plus ancien évincé
    assert await store.get("b") == 2
    assert await store.get("c") == 3


async def test_get_promotes_recency():
    store = InMemoryLRUStore(max_size=2)
    await store.put("a", 1)
    await store.put("b", 2)
    await store.get("a")  # promote a
    await store.put("c", 3)
    assert await store.get("a") == 1  # a survit
    assert await store.get("b") is None


async def test_clear_drops_all():
    store = InMemoryLRUStore(max_size=4)
    await store.put("a", 1)
    await store.put("b", 2)
    await store.clear()
    assert await store.get("a") is None
    assert await store.get("b") is None


async def test_evict_specific():
    store = InMemoryLRUStore(max_size=4)
    await store.put("a", 1)
    await store.put("b", 2)
    await store.evict("a")
    assert await store.get("a") is None
    assert await store.get("b") == 2


def test_zero_max_size_rejected():
    with pytest.raises(ValueError):
        InMemoryLRUStore(max_size=0)


async def test_concurrent_put_safe():
    store = InMemoryLRUStore(max_size=100)
    await asyncio.gather(*[store.put(f"k{i}", i) for i in range(50)])
    values = await asyncio.gather(*[store.get(f"k{i}") for i in range(50)])
    assert values == list(range(50))
