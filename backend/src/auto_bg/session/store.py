import asyncio
from collections import OrderedDict
from typing import Any, Protocol


class EmbeddingStore(Protocol):
    """Cache abstrait d'embeddings opaques indexés par session_id.

    L'implémentation concrète n'a pas à connaître la nature de la valeur :
    pour SAM 2 c'est le state du predictor après set_image,
    pour le mock c'est juste l'image numpy.
    """

    async def put(self, session_id: str, value: Any) -> None: ...
    async def get(self, session_id: str) -> Any | None: ...
    async def evict(self, session_id: str) -> None: ...
    async def clear(self) -> None: ...
    async def has(self, session_id: str) -> bool: ...


class InMemoryLRUStore:
    """LRU bornée, thread-safe via asyncio.Lock."""

    def __init__(self, max_size: int = 8) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._lru: "OrderedDict[str, Any]" = OrderedDict()
        self._lock = asyncio.Lock()
        self._max_size = max_size

    async def put(self, session_id: str, value: Any) -> None:
        async with self._lock:
            if session_id in self._lru:
                self._lru.move_to_end(session_id)
            self._lru[session_id] = value
            while len(self._lru) > self._max_size:
                self._lru.popitem(last=False)

    async def get(self, session_id: str) -> Any | None:
        async with self._lock:
            if session_id not in self._lru:
                return None
            self._lru.move_to_end(session_id)
            return self._lru[session_id]

    async def evict(self, session_id: str) -> None:
        async with self._lock:
            self._lru.pop(session_id, None)

    async def clear(self) -> None:
        async with self._lock:
            self._lru.clear()

    async def has(self, session_id: str) -> bool:
        async with self._lock:
            return session_id in self._lru
