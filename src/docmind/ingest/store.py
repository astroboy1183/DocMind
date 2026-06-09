from typing import Protocol

from docmind.types import Chunk


class VectorStore(Protocol):
    """Contract: store chunks + their vectors, and let us read them back."""

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...
    def all(self) -> list[tuple[Chunk, list[float]]]: ...


class InMemoryStore:
    """Skeleton-only: a list in memory. Swapped for Chroma later."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[Chunk, list[float]]] = {}

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        for chunk, vector in zip(chunks, vectors, strict=True):
            self._data[chunk.chunk_id] = (chunk, vector)  # keyed by id = idempotent

    def all(self) -> list[tuple[Chunk, list[float]]]:
        return list(self._data.values())
