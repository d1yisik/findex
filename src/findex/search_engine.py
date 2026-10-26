from __future__ import annotations

from typing import Any, Literal, Sequence

from findex.models import Posting


class BooleanSearchEngine:
    """Булевий пошуковий рушій (Merge vs Set)."""

    def __init__(self, index: Any, engine: Literal["merge", "set"] = "merge") -> None:
        self.index: Any = index
        self.engine: Literal["merge", "set"] = engine

    def _get_postings(self, term: str) -> list[Posting]:
        internal_idx: dict[str, list[Posting]] = getattr(self.index, "_index", {})
        if term.lower() in internal_idx:
            return internal_idx[term.lower()]
        if hasattr(self.index, "get"):
            res: list[Posting] = self.index.get(term.lower(), [])
            return res
        return []

    def search_and(self, terms: Sequence[str]) -> list[int]:
        if not terms:
            return []

        if self.engine == "set":
            return self._search_and_set(terms)
        return self._search_and_merge(terms)

    def _search_and_set(self, terms: Sequence[str]) -> list[int]:
        first_postings = self._get_postings(terms[0])
        res_set: set[int] = {p.doc_id for p in first_postings}

        for term in terms[1:]:
            current_postings = self._get_postings(term)
            current_set: set[int] = {p.doc_id for p in current_postings}
            res_set &= current_set

        return sorted(res_set)

    def _search_and_merge(self, terms: Sequence[str]) -> list[int]:
        postings_list = [self._get_postings(t) for t in terms]
        if not postings_list or any(len(p) == 0 for p in postings_list):
            return []

        postings_list.sort(key=len)
        result: list[int] = [p.doc_id for p in postings_list[0]]

        for next_postings in postings_list[1:]:
            next_ids: list[int] = [p.doc_id for p in next_postings]
            i, j = 0, 0
            merged: list[int] = []
            while i < len(result) and j < len(next_ids):
                if result[i] == next_ids[j]:
                    merged.append(result[i])
                    i += 1
                    j += 1
                elif result[i] < next_ids[j]:
                    i += 1
                else:
                    j += 1
            result = merged

        return result

    def search(self, query: str) -> list[int]:
        terms = query.lower().split()
        return self.search_and(terms)