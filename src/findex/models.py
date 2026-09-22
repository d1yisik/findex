from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Posting:
    __slots__ = ("doc_id", "tf", "positions")
    doc_id: int
    tf: int
    positions: tuple[int, ...]

    def __getstate__(self):
        return (self.doc_id, self.tf, self.positions)

    def __setstate__(self, state):
        object.__setattr__(self, "doc_id", state[0])
        object.__setattr__(self, "tf", state[1])
        object.__setattr__(self, "positions", state[2])


@dataclass(frozen=True)
class DocMeta:
    __slots__ = ("doc_id", "path", "length")
    doc_id: int
    path: str
    length: int

    def __getstate__(self):
        return (self.doc_id, self.path, self.length)

    def __setstate__(self, state):
        object.__setattr__(self, "doc_id", state[0])
        object.__setattr__(self, "path", state[1])
        object.__setattr__(self, "length", state[2])


@dataclass(order=True)
class SearchResult:
    score: float
    doc_id: int = field(compare=False)
    path: str = field(compare=False)
    snippet: str = field(default="", compare=False)