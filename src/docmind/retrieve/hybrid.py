from docmind.types import Passage


def reciprocal_rank_fusion(ranked_lists: list[list[Passage]], k: int = 60) -> list[Passage]:
    """Fuse several ranked passage lists via Reciprocal Rank Fusion.

    score(chunk) = sum over lists of 1 / (k + rank). Rank-based, so it needs no
    score normalization between dense (cosine) and keyword (BM25) — that's why
    RRF is the standard hybrid fuser. Dedupes by chunk_id.
    """
    scores: dict[str, float] = {}
    first_seen: dict[str, Passage] = {}
    for passages in ranked_lists:
        for rank, passage in enumerate(passages):
            cid = passage.chunk.chunk_id
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
            first_seen.setdefault(cid, passage)

    fused = [Passage(chunk=first_seen[cid].chunk, score=score) for cid, score in scores.items()]
    fused.sort(key=lambda passage: -passage.score)
    return fused
