from __future__ import annotations

import collections.abc
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
import pickle

from findex.corpus import iter_documents
from findex.models import DocMeta, Posting
from findex.tokenizer import tokenize


class Index(collections.abc.Mapping):
    """Повноцінний ідіоматичний індекс як Mapping."""

    def __init__(self):
        self._index: dict[str, list[Posting]] = {}
        self.documents: dict[int, DocMeta] = {}

    def __getitem__(self, term: str) -> list[Posting]:
        return self._index[term.lower()]

    def __iter__(self):
        return iter(self._index)

    def __len__(self) -> int:
        return len(self._index)

    def __contains__(self, term: object) -> bool:
        if not isinstance(term, str):
            return False
        return term.lower() in self._index

    def __repr__(self) -> str:
        return f"<Index terms={len(self._index)} docs={len(self.documents)} avg_len={self.avg_doc_length:.1f}>"

    @property
    def num_docs(self) -> int:
        return len(self.documents)

    @cached_property
    def avg_doc_length(self) -> float:
        if not self.documents:
            return 0.0
        return sum(doc.length for doc in self.documents.values()) / len(self.documents)

    def df(self, term: str) -> int:
        postings = self._index.get(term.lower())
        return len(postings) if postings else 0

    def get_postings(self, term: str) -> list[Posting]:
        return self._index.get(term.lower(), [])

    def build_from_corpus(self, folder_path: str | Path) -> None:
        doc_id = 0
        for filename, text in iter_documents(folder_path):
            tokens = tokenize(text)
            self.documents[doc_id] = DocMeta(
                doc_id=doc_id, path=filename, length=len(tokens)
            )

            positions_map: dict[str, list[int]] = {}
            for pos, tok in enumerate(tokens):
                positions_map.setdefault(tok, []).append(pos)

            for term, positions in positions_map.items():
                if term not in self._index:
                    self._index[term] = []
                self._index[term].append(
                    Posting(doc_id=doc_id, tf=len(positions), positions=tuple(positions))
                )
            doc_id += 1

    def save_pickle(self, file_path: str | Path) -> None:
        with open(file_path, "wb") as f:
            pickle.dump((self.documents, self._index), f)

    @classmethod
    def load_pickle(cls, file_path: str | Path) -> Index:
        idx = cls()
        with open(file_path, "rb") as f:
            documents, index_dict = pickle.load(f)
        idx.documents = documents
        idx._index = index_dict
        return idx


InvertedIndex = Index


@contextmanager
def open_index(path: str | Path):
    idx = None
    try:
        idx = Index.load_pickle(path)
        yield idx
    finally:
        if idx is not None:
            idx.documents.clear()
            idx._index.clear()