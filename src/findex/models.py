from dataclasses import dataclass


@dataclass(frozen=True)
class Posting:
    __slots__ = ("doc_id", "tf")
    doc_id: int
    tf: int

    def __getstate__(self):
        return (self.doc_id, self.tf)

    def __setstate__(self, state):
        object.__setattr__(self, "doc_id", state[0])
        object.__setattr__(self, "tf", state[1])


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