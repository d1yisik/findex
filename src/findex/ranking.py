from __future__ import annotations

import math
from typing import Any, Literal, Protocol, Sequence

from findex.models import Posting, SearchResult

EngineType = Literal["bm25", "tfidf"]


class Scorer(Protocol):
    """Protocol для pyright strict без наслідування."""

    def score(
        self, tf: int, df: int, total_docs: int, doc_len: int, avg_len: float
    ) -> float:
        ...


class BM25Scorer:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

    def score(
        self, tf: int, df: int, total_docs: int, doc_len: int, avg_len: float
    ) -> float:
        idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
        denom = tf + self.k1 * (1 - self.b + self.b * (doc_len / (avg_len or 1.0)))
        return idf * (tf * (self.k1 + 1)) / (denom or 1.0)


class TFIDFScorer:
    def score(
        self, tf: int, df: int, total_docs: int, doc_len: int, avg_len: float
    ) -> float:
        tf_val = tf / (doc_len or 1.0)
        idf_val = math.log((total_docs + 1.0) / (df + 1.0)) + 1.0
        return tf_val * idf_val


class BM25:
    def __init__(self, index: Any, k1: float = 1.5, b: float = 0.75) -> None:
        self.index: Any = index
        self.k1 = k1
        self.b = b

    def score_term(self, term: str, tf: int, doc_len: int) -> float:
        documents: dict[int, Any] = getattr(self.index, "documents", {})
        total_docs = len(documents)
        avg_len = float(getattr(self.index, "avg_doc_length", 1.0))
        postings_raw: list[Posting] = getattr(self.index, "_index", {}).get(term, [])
        df = len(postings_raw)
        scorer = BM25Scorer(self.k1, self.b)
        return scorer.score(tf, df, total_docs, doc_len, avg_len)


class TfIdf:
    def __init__(self, index: Any) -> None:
        self.index: Any = index

    def score_term(self, term: str, tf: int, doc_len: int) -> float:
        documents: dict[int, Any] = getattr(self.index, "documents", {})
        total_docs = len(documents)
        avg_len = float(getattr(self.index, "avg_doc_length", 1.0))
        postings_raw: list[Posting] = getattr(self.index, "_index", {}).get(term, [])
        df = len(postings_raw)
        scorer = TFIDFScorer()
        return scorer.score(tf, df, total_docs, doc_len, avg_len)


def rank_documents(
    index: Any,
    terms: Sequence[str],
    matched_docs: set[int],
    scorer: Any,
    top_k: int = 10,
) -> list[SearchResult]:
    results: list[SearchResult] = []
    documents: dict[int, Any] = getattr(index, "documents", {})

    for doc_id in matched_docs:
        meta = documents.get(doc_id)
        if not meta:
            continue
        total_score = 0.0
        for term in terms:
            postings: list[Posting] = getattr(index, "_index", {}).get(term, [])
            for p in postings:
                if p.doc_id == doc_id:
                    total_score += scorer.score_term(term, p.tf, meta.length)

        results.append(SearchResult(score=round(total_score, 4), doc_id=doc_id, path=meta.path))

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:top_k]