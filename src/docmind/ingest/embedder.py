from typing import Protocol


class Embedder(Protocol):
    """Contract: turn texts into vectors. Any embedder must match this shape."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class FakeEmbedder:
    """Skeleton-only: returns trivial deterministic vectors (no real meaning)."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        # 2-dim 'vector': [length, word-count]. Just proves the wiring works.
        return [[float(len(t)), float(t.count(" ") + 1)] for t in texts]
