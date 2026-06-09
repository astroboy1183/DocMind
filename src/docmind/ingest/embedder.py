from functools import cached_property
from typing import Protocol

from docmind.config import settings


class Embedder(Protocol):
    """Contract: turn texts into vectors. Any embedder must match this shape."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class FakeEmbedder:
    """Skeleton-only: returns trivial deterministic vectors (no real meaning)."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        # 2-dim 'vector': [length, word-count]. Just proves the wiring works.
        return [[float(len(t)), float(t.count(" ") + 1)] for t in texts]


class SentenceTransformerEmbedder:
    """Real embedder: wraps a sentence-transformers model (default from config)."""

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or settings.embedding_model

    @cached_property
    def _model(self):
        # Lazy + heavy: importing torch/sbert is slow, so we defer it out of
        # module-import time and load the model once, on first use.
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(self._model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(
            texts,
            batch_size=32,  # batch the calls
            normalize_embeddings=True,  # unit vectors → cosine == dot product
            convert_to_numpy=True,
        )
        return vectors.tolist()  # honor the Protocol: list[list[float]]
