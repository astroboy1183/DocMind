from dataclasses import dataclass, field


@dataclass(frozen=True)
class Document:
    doc_id: str
    source_path: str
    content_hash: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    metadata: dict = field(default_factory=dict)  # page, section, position...


@dataclass(frozen=True)
class Passage:  # a retrieved chunk + why
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Citation:
    marker: str  # e.g. "[1]"
    chunk_id: str
    source_path: str


@dataclass(frozen=True)
class Answer:
    text: str
    citations: list[Citation] = field(default_factory=list)
