from __future__ import annotations

import collections.abc
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from functools import cached_property
import json
from pathlib import Path
import pickle

from findex.corpus import iter_documents
from findex.models import DocMeta, Posting
from findex.tokenizer import tokenize


class IndexMapping(collections.abc.Mapping[str, list[Posting]]):
    """Повноцінний ідіоматичний індекс як Mapping."""

    def __init__(self) -> None:
        self._index: dict[str, list[Posting]] = {}
        self.documents: dict[int, DocMeta] = {}

    def __getitem__(self, term: str) -> list[Posting]:
        return self._index[term.lower()]

    def __iter__(self) -> Iterator[str]:
        return iter(self._index)

    def __len__(self) -> int:
        return len(self._index)

    def __contains__(self, term: object) -> bool:
        if not isinstance(term, str):
            return False
        return term.lower() in self._index

    @cached_property
    def avg_doc_length(self) -> float:
        if not self.documents:
            return 0.0
        total_len = sum(doc.length for doc in self.documents.values())
        return total_len / len(self.documents)

    def build_from_corpus(self, corpus_path: str | Path) -> None:
        doc_id_counter = 0
        for filename, text in iter_documents(corpus_path):
            tokens = tokenize(text)
            doc_meta = DocMeta(doc_id=doc_id_counter, path=filename, length=len(tokens))
            self.documents[doc_id_counter] = doc_meta

            positions_map: dict[str, list[int]] = {}
            for pos, token in enumerate(tokens):
                positions_map.setdefault(token, []).append(pos)

            for token, positions in positions_map.items():
                posting = Posting(
                    doc_id=doc_id_counter,
                    tf=len(positions),
                    positions=tuple(positions),
                )
                self._index.setdefault(token, []).append(posting)

            doc_id_counter += 1

    def save_pickle(self, path: str | Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load_pickle(path: str | Path) -> IndexMapping:
        with open(path, "rb") as f:
            return pickle.load(f)  # type: ignore[no-any-return]

    def save_json(self, path: str | Path) -> None:
        data = {
            "documents": {
                str(k): {"path": v.path, "length": v.length}
                for k, v in self.documents.items()
            },
            "index": {
                term: [{"doc_id": p.doc_id, "tf": p.tf} for p in postings]
                for term, postings in self._index.items()
            },
        }
        Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def load_json(path: str | Path) -> IndexMapping:
        idx = IndexMapping()
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        for k, v in raw.get("documents", {}).items():
            idx.documents[int(k)] = DocMeta(
                doc_id=int(k), path=v["path"], length=v["length"]
            )
        for term, postings in raw.get("index", {}).items():
            idx._index[term] = [
                Posting(doc_id=p["doc_id"], tf=p["tf"], positions=tuple(p.get("positions", ())))
                for p in postings
            ]
        return idx


InvertedIndex = IndexMapping
Index = IndexMapping


@contextmanager
def open_index(path: str | Path) -> Generator[IndexMapping, None, None]:
    p = Path(path)
    if p.suffix == ".json":
        idx = IndexMapping.load_json(p)
    else:
        idx = IndexMapping.load_pickle(p)
    try:
        yield idx
    finally:
        pass