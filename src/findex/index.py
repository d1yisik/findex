from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator, KeysView

from findex.models import DocMeta, Posting


class IndexMapping:
    """Represents the inverted index mapping terms to postings and document titles/metadata."""

    def __init__(self) -> None:
        self._index: dict[str, list[Posting]] = {}
        self.doc_titles: dict[int, str] = {}
        self.documents: dict[int, DocMeta] = {}

    def __contains__(self, term: str) -> bool:
        return term in self._index or term.lower() in self._index

    def __getitem__(self, term: str) -> list[Posting]:
        if term in self._index:
            return self._index[term]
        return self._index.get(term.lower(), [])

    def __iter__(self) -> Iterator[str]:
        return iter(self._index)

    def __len__(self) -> int:
        return len(self._index)

    def keys(self) -> KeysView[str]:
        return self._index.keys()

    @property
    def avg_doc_length(self) -> float:
        if not self.documents:
            return 0.0
        return sum(d.length for d in self.documents.values()) / len(self.documents)

    def add_posting(self, term: str, posting: Posting) -> None:
        key = term
        if key not in self._index:
            self._index[key] = []
        self._index[key].append(posting)

    def get_postings(self, term: str) -> list[Posting]:
        if term in self._index:
            return self._index[term]
        return self._index.get(term.lower(), [])

    def build_from_corpus(self, corpus_dir: Path) -> None:
        """Сумісність зі старими тестами побудови з корпусу."""
        from findex.builder import build_index_parallel
        res = build_index_parallel(corpus_dir, workers=1, executor_type="serial")
        self._index = res._index  # pyright: ignore[reportPrivateUsage]
        self.doc_titles = res.doc_titles
        for doc_id, title in self.doc_titles.items():
            self.documents[doc_id] = DocMeta(doc_id=doc_id, path=title, length=10)

    def save_json(self, path: Path) -> None:
        import json

        def posting_to_dict(p: Any) -> dict[str, Any]:
            if hasattr(p, "__dict__"):
                return dict(p.__dict__)
            if hasattr(p, "doc_id") and hasattr(p, "tf") and hasattr(p, "positions"):
                return {"doc_id": p.doc_id, "tf": p.tf, "positions": list(p.positions)}
            return {"doc_id": p[0], "tf": p[1], "positions": list(p[2])}

        data = {
            "index": {
                term: [posting_to_dict(p) for p in postings]
                for term, postings in self._index.items()
            },
            "doc_titles": {str(k): v for k, v in self.doc_titles.items()},
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_pickle(self, path: Path) -> None:
        import pickle

        path.write_bytes(pickle.dumps(self))

    @classmethod
    def load_json(cls, path: Path) -> IndexMapping:
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        instance = cls()
        instance._index = {
            term: [Posting(**p) for p in postings]
            for term, postings in data.get("index", {}).items()
        }
        instance.doc_titles = {int(k): v for k, v in data.get("doc_titles", {}).items()}
        return instance

    @classmethod
    def load_pickle(cls, path: Path) -> IndexMapping:
        import pickle

        loaded = pickle.loads(path.read_bytes())
        if isinstance(loaded, cls):
            return loaded
        raise TypeError("Invalid pickle data for IndexMapping")