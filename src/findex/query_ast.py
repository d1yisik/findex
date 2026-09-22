from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from findex.builder import Index


class Node(ABC):
    @abstractmethod
    def evaluate(self, index: Index) -> set[int]:
        """Обчислює множину doc_id для цього вузла."""
        ...

    def __and__(self, other: Node) -> And:
        return And(self, other)

    def __or__(self, other: Node) -> Or:
        return Or(self, other)

    def __invert__(self) -> Not:
        return Not(self)


class Term(Node):
    def __init__(self, value: str):
        self.value = value.lower()

    def evaluate(self, index: Index) -> set[int]:
        postings = index.get_postings(self.value)
        return {p.doc_id for p in postings}

    def __repr__(self) -> str:
        return f"Term({self.value!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Term) and self.value == other.value


class Phrase(Node):
    def __init__(self, phrase: str):
        self.words = [w.lower() for w in phrase.strip().split() if w]

    def evaluate(self, index: Index) -> set[int]:
        if not self.words:
            return set()
        if len(self.words) == 1:
            return Term(self.words[0]).evaluate(index)

        # Знаходимо спільні документи для всіх слів фрази
        first_postings = {p.doc_id: set(p.positions) for p in index.get_postings(self.words[0])}
        doc_candidates = set(first_postings.keys())

        for word in self.words[1:]:
            w_postings = {p.doc_id: set(p.positions) for p in index.get_postings(word)}
            doc_candidates &= set(w_postings.keys())

        matched_docs = set()
        for doc_id in doc_candidates:
            # Перевіряємо послідовність позицій слів
            current_positions = first_postings[doc_id]
            for offset, word in enumerate(self.words[1:], start=1):
                w_pos = {p.doc_id: set(p.positions) for p in index.get_postings(word)}[doc_id]
                next_positions = {p + 1 for p in current_positions if (p + 1) in w_pos}
                current_positions = next_positions
                if not current_positions:
                    break
            if current_positions:
                matched_docs.add(doc_id)

        return matched_docs

    def __repr__(self) -> str:
        return f"Phrase({' '.join(self.words)!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Phrase) and self.words == other.words


class And(Node):
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def evaluate(self, index: Index) -> set[int]:
        return self.left.evaluate(index) & self.right.evaluate(index)

    def __repr__(self) -> str:
        return f"And({self.left!r}, {self.right!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, And) and self.left == other.left and self.right == other.right


class Or(Node):
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def evaluate(self, index: Index) -> set[int]:
        return self.left.evaluate(index) | self.right.evaluate(index)

    def __repr__(self) -> str:
        return f"Or({self.left!r}, {self.right!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Or) and self.left == other.left and self.right == other.right


class Not(Node):
    def __init__(self, child: Node):
        self.child = child

    def evaluate(self, index: Index) -> set[int]:
        all_docs = set(index.documents.keys())
        return all_docs - self.child.evaluate(index)

    def __repr__(self) -> str:
        return f"Not({self.child!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Not) and self.child == other.child


# --- Парсер рекурсивного спуску ---

class QueryParser:
    """
    Граматика:
      expr     := or_expr
      or_expr  := and_expr ('OR' and_expr)*
      and_expr := not_expr (['AND'] not_expr)*
      not_expr := 'NOT' not_expr | atom
      atom     := '(' expr ')' | '"' phrase '"' | term
    """

    def __init__(self, query: str):
        self.tokens = self._tokenize(query)
        self.pos = 0

    def _tokenize(self, query: str) -> list[str]:
        # Розбиває на токени: фрази в лапках, дужки, слова
        token_pattern = r'\"[^\"]+\"|\(|\)|[^\s()\"]+'
        return re.findall(token_pattern, query)

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _consume(self) -> str:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse(self) -> Node:
        node = self._parse_or()
        return node

    def _parse_or(self) -> Node:
        node = self._parse_and()
        while self._peek() == "OR":
            self._consume()
            right = self._parse_and()
            node = Or(node, right)
        return node

    def _parse_and(self) -> Node:
        node = self._parse_not()
        while self._peek() and self._peek() not in (")", "OR"):
            if self._peek() == "AND":
                self._consume()
            right = self._parse_not()
            node = And(node, right)
        return node

    def _parse_not(self) -> Node:
        if self._peek() == "NOT":
            self._consume()
            return Not(self._parse_not())
        return self._parse_atom()

    def _parse_atom(self) -> Node:
        tok = self._peek()
        if tok == "(":
            self._consume()
            node = self._parse_or()
            if self._peek() == ")":
                self._consume()
            return node
        elif tok and tok.startswith('"') and tok.endswith('"'):
            self._consume()
            return Phrase(tok[1:-1])
        elif tok:
            self._consume()
            return Term(tok)
        raise ValueError("Неочікуваний кінець запиту")


def parse_query(query: str) -> Node:
    return QueryParser(query).parse()