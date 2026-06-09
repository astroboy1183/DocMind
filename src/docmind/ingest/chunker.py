from docmind.types import Chunk


def chunk_text(text: str, doc_id: str, size: int = 400, overlap: int = 50) -> list[Chunk]:
    """Skeleton chunker: fixed-size character windows with overlap.
    Crude on purpose — we make it structure-aware later."""
    if overlap >= size:
        raise ValueError(f"overlap ({overlap}) must be < size ({size})")
    chunks: list[Chunk] = []
    start, position = 0, 0
    while start < len(text):
        piece = text[start : start + size]
        chunks.append(
            Chunk(
                chunk_id=f"{doc_id}:{position}",
                doc_id=doc_id,
                text=piece,
                metadata={"position": position},
            )
        )
        start += size - overlap
        position += 1
    return chunks
