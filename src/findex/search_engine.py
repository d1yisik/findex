from __future__ import annotations

from findex.builder import InvertedIndex


def merge_and(postings_a: list[int], postings_b: list[int]) -> list[int]:
    """Перетин двох відсортованих списків doc_id через два вказівники."""
    result = []
    i, j = 0, 0
    while i < len(postings_a) and j < len(postings_b):
        doc_a = postings_a[i]
        doc_b = postings_b[j]
        if doc_a == doc_b:
            result.append(doc_a)
            i += 1
            j += 1
        elif doc_a < doc_b:
            i += 1
        else:
            j += 1
    return result


def merge_or(postings_a: list[int], postings_b: list[int]) -> list[int]:
    """Об'єднання двох відсортованих списків doc_id через два вказівники."""
    result = []
    i, j = 0, 0
    while i < len(postings_a) and j < len(postings_b):
        doc_a = postings_a[i]
        doc_b = postings_b[j]
        if doc_a == doc_b:
            result.append(doc_a)
            i += 1
            j += 1
        elif doc_a < doc_b:
            result.append(doc_a)
            i += 1
        else:
            result.append(doc_b)
            j += 1
    while i < len(postings_a):
        result.append(postings_a[i])
        i += 1
    while j < len(postings_b):
        result.append(postings_b[j])
        j += 1
    return result


def merge_not(all_docs: list[int], postings: list[int]) -> list[int]:
    """Різниця (all_docs AND NOT postings) через два вказівники."""
    result = []
    i, j = 0, 0
    while i < len(all_docs) and j < len(postings):
        doc_all = all_docs[i]
        doc_p = postings[j]
        if doc_all == doc_p:
            i += 1
            j += 1
        elif doc_all < doc_p:
            result.append(doc_all)
            i += 1
        else:
            j += 1
    while i < len(all_docs):
        result.append(all_docs[i])
        i += 1
    return result


class BooleanSearchEngine:
    def __init__(self, index: InvertedIndex, engine: str = "merge"):
        self.index = index
        self.engine = engine
        self.all_doc_ids = sorted(index.documents.keys())

    def _get_doc_ids(self, term: str) -> list[int]:
        postings = self.index.index.get(term.lower(), [])
        return [p.doc_id for p in postings]

    def search(self, query: str) -> list[int]:
        tokens = query.strip().split()
        if not tokens:
            return []

        # Парсинг запиту з підтримкою OR та NOT
        terms = []
        operators = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok in ("OR", "NOT"):
                operators.append(tok)
                i += 1
            else:
                terms.append(tok)
                if i > 0 and tokens[i - 1] not in ("OR", "NOT"):
                    operators.append("AND")
                i += 1

        if self.engine == "set":
            return self._search_set(tokens)
        return self._search_merge(tokens)

    def _search_merge(self, tokens: list[str]) -> list[int]:
        current_res = None
        current_op = "AND"
        is_not = False

        for tok in tokens:
            if tok.upper() == "AND":
                current_op = "AND"
                continue
            if tok.upper() == "OR":
                current_op = "OR"
                continue
            if tok.upper() == "NOT":
                is_not = True
                continue

            doc_ids = self._get_doc_ids(tok.lower())
            if is_not:
                doc_ids = merge_not(self.all_doc_ids, doc_ids)
                is_not = False

            if current_res is None:
                current_res = doc_ids
            else:
                if current_op == "AND":
                    current_res = merge_and(current_res, doc_ids)
                elif current_op == "OR":
                    current_res = merge_or(current_res, doc_ids)

        return current_res if current_res is not None else []

    def _search_set(self, tokens: list[str]) -> list[int]:
        all_docs_set = set(self.all_doc_ids)
        current_res = None
        current_op = "AND"
        is_not = False

        for tok in tokens:
            if tok.upper() == "AND":
                current_op = "AND"
                continue
            if tok.upper() == "OR":
                current_op = "OR"
                continue
            if tok.upper() == "NOT":
                is_not = True
                continue

            doc_set = set(self._get_doc_ids(tok.lower()))
            if is_not:
                doc_set = all_docs_set - doc_set
                is_not = False

            if current_res is None:
                current_res = doc_set
            else:
                if current_op == "AND":
                    current_res = current_res & doc_set
                elif current_op == "OR":
                    current_res = current_res | doc_set

        return sorted(current_res) if current_res is not None else []

    def _search_set(self, tokens: list[str]) -> list[int]:
        all_docs_set = set(self.all_doc_ids)
        current_res = None
        current_op = "AND"
        is_not = False

        for tok in tokens:
            if tok == "AND":
                current_op = "AND"
                continue
            if tok == "OR":
                current_op = "OR"
                continue
            if tok == "NOT":
                is_not = True
                continue

            doc_set = set(self._get_doc_ids(tok))
            if is_not:
                doc_set = all_docs_set - doc_set
                is_not = False

            if current_res is None:
                current_res = doc_set
            else:
                if current_op == "AND":
                    current_res = current_res & doc_set
                elif current_op == "OR":
                    current_res = current_res | doc_set

        return sorted(current_res) if current_res is not None else []