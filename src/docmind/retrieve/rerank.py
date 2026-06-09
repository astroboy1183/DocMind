from functools import cached_property

from docmind.config import settings
from docmind.types import Passage


class CrossEncoderReranker:
    """Re-scores (query, chunk) pairs together with a cross-encoder, which is far
    more precise than the bi-encoder similarity used for first-pass retrieval.

    The pattern: retrieve a wide set cheaply, rerank a small set expensively.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or settings.reranker_model

    @cached_property
    def _model(self):
        # Lazy + heavy: defer the torch/sbert import and model load to first use.
        from sentence_transformers import CrossEncoder

        return CrossEncoder(self._model_name)

    def rerank(self, query: str, passages: list[Passage], top_n: int = 5) -> list[Passage]:
        if not passages:
            return []

        pairs = [(query, passage.chunk.text) for passage in passages]
        scores = self._model.predict(pairs)
        rescored = [
            Passage(chunk=passage.chunk, score=float(score))
            for passage, score in zip(passages, scores, strict=True)
        ]
        rescored.sort(key=lambda passage: -passage.score)
        return rescored[:top_n]
