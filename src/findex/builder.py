from __future__ import annotations
import json
import pickle
from collections import Counter, defaultdict
from pathlib import Path

from findex.corpus import iter_documents
from findex.models import DocMeta, Posting
from findex.tokenizer import tokenize


class InvertedIndex:
    def __init__(self):
        # term -> list[Posting]
        self.index: dict[str, list[Posting]] = defaultdict(list)
        # doc_id -> DocMeta
        self.documents: dict[int, DocMeta] = {}

    def build_from_corpus(self, folder_path: str | Path) -> None:
        """Лениво строит индекс в один проход по документам корпуса."""
        doc_id = 0
        for filename, text in iter_documents(folder_path):
            tokens = tokenize(text)
            self.documents[doc_id] = DocMeta(
                doc_id=doc_id, path=filename, length=len(tokens)
            )

            counts = Counter(tokens)
            for term, tf in counts.items():
                self.index[term].append(Posting(doc_id=doc_id, tf=tf))

            doc_id += 1

    def save_pickle(self, file_path: str | Path) -> None:
        """Сохраняет состояние индекса через pickle."""
        with open(file_path, "wb") as f:
            pickle.dump((self.documents, dict(self.index)), f)

    @classmethod
    def load_pickle(cls, file_path: str | Path) -> "InvertedIndex":
        """Загружает состояние индекса из pickle-файла."""
        idx = cls()
        with open(file_path, "rb") as f:
            documents, index = pickle.load(f)
        idx.documents = documents
        idx.index = defaultdict(list, index)
        return idx

    def save_json(self, file_path: str | Path) -> None:
        """Сохраняет состояние индекса в JSON (второй формат)."""
        data = {
            "documents": {
                doc_id: {"path": meta.path, "length": meta.length}
                for doc_id, meta in self.documents.items()
            },
            "index": {
                term: [{"doc_id": p.doc_id, "tf": p.tf} for p in postings]
                for term, postings in self.index.items()
            },
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    @classmethod
    def load_json(cls, file_path: str | Path) -> "InvertedIndex":
        """Загружает состояние индекса из JSON."""
        idx = cls()
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        idx.documents = {
            int(doc_id): DocMeta(
                doc_id=int(doc_id), path=meta["path"], length=meta["length"]
            )
            for doc_id, meta in data["documents"].items()
        }

        idx.index = defaultdict(list)
        for term, postings in data["index"].items():
            idx.index[term] = [
                Posting(doc_id=p["doc_id"], tf=p["tf"]) for p in postings
            ]

        return idx