from __future__ import annotations

import heapq
import math
from typing import Protocol, runtime_checkable

from findex.builder import Index
from findex.models import SearchResult


@runtime_checkable
class Scorer(Protocol):
    def score_term(self, term: str, tf: int, doc_len: int) -> float:
        ...


class TfIdf:
    def __init__(self, index: Index):
        self.index = index
        self.num_docs = index.num_docs

    def idf(self, term: str) -> float:
        df = self.index.df(term)
        if df == 0:
            return 0.0
        return math.log((self.num_docs + 1) / (df + 0.5)) + 1.0

    def score_term(self, term: str, tf: int, doc_len: int) -> float:
        if tf == 0:
            return 0.0
        tf_norm = tf / doc_len if doc_len > 0 else 0.0
        return tf_norm * self.idf(term)


class BM25:
    def __init__(self, index: Index, k1: float = 1.5, b: float = 0.75):
        self.index = index
        self.k1 = k1
        self.b = b
        self.num_docs = index.num_docs
        self.avg_doc_len = index.avg_doc_length

    def idf(self, term: str) -> float:
        df = self.index.df(term)
        if df == 0:
            return 0.0
        val = (self.num_docs - df + 0.5) / (df + 0.5)
        return math.log(1.0 + max(val, 0.0))

    def score_term(self, term: str, tf: int, doc_len: int) -> float:
        if tf == 0:
            return 0.0
        idf_val = self.idf(term)
        len_norm = 1.0 - self.b + self.b * (doc_len / self.avg_doc_len if self.avg_doc_len > 0 else 1.0)
        denom = tf + self.k1 * len_norm
        return idf_val * ((tf * (self.k1 + 1.0)) / denom)


def rank_documents(
    index: Index,
    query_terms: list[str],
    matched_doc_ids: set[int] | list[int],
    scorer: Scorer,
    top_k: int = 5,
) -> list[SearchResult]:
    scores: dict[int, float] = {doc_id: 0.0 for doc_id in matched_doc_ids}

    for term in query_terms:
        postings = index.get_postings(term)
        postings_map = {p.doc_id: p.tf for p in postings}

        for doc_id in scores:
            tf = postings_map.get(doc_id, 0)
            if tf > 0:
                doc_len = index.documents[doc_id].length
                scores[doc_id] += scorer.score_term(term, tf, doc_len)

    results = [
        SearchResult(
            score=score,
            doc_id=doc_id,
            path=index.documents[doc_id].path,
        )
        for doc_id, score in scores.items()
    ]

    return heapq.nlargest(top_k, results)