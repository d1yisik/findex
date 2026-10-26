from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from findex.models import Posting


class ASTNode(ABC):
    @abstractmethod
    def evaluate(self, index: Any) -> set[int]:
        ...

    def __and__(self, other: ASTNode) -> And:
        return And(self, other)

    def __or__(self, other: ASTNode) -> Or:
        return Or(self, other)

    def __invert__(self) -> Not:
        return Not(self)


class Term(ASTNode):
    def __init__(self, term: str) -> None:
        self.term = term.lower()

    def evaluate(self, index: Any) -> set[int]:
        postings: list[Posting] = getattr(index, "_index", {}).get(self.term, [])
        if not postings and hasattr(index, "get"):
            postings = index.get(self.term, [])
        return {p.doc_id for p in postings}

    def __repr__(self) -> str:
        return f"Term({self.term!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Term):
            return False
        return self.term == other.term


class Phrase(ASTNode):
    def __init__(self, phrase: str) -> None:
        self.words = [w.lower() for w in phrase.split()]

    def evaluate(self, index: Any) -> set[int]:
        if not self.words:
            return set()

        doc_positions: dict[int, dict[str, set[int]]] = {}
        for word in self.words:
            postings: list[Posting] = getattr(index, "_index", {}).get(word, [])
            for p in postings:
                if p.doc_id not in doc_positions:
                    doc_positions[p.doc_id] = {}
                doc_positions[p.doc_id][word] = set(p.positions)

        matched_docs: set[int] = set()
        for doc_id, positions_map in doc_positions.items():
            if len(positions_map) < len(self.words):
                continue

            first_word_positions = positions_map[self.words[0]]
            for start_pos in first_word_positions:
                match = True
                for i, word in enumerate(self.words[1:], start=1):
                    if (start_pos + i) not in positions_map[word]:
                        match = False
                        break
                if match:
                    matched_docs.add(doc_id)
                    break

        return matched_docs

    def __repr__(self) -> str:
        return f"Phrase({' '.join(self.words)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Phrase):
            return False
        return self.words == other.words


class And(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode) -> None:
        self.left = left
        self.right = right

    def evaluate(self, index: Any) -> set[int]:
        return self.left.evaluate(index) & self.right.evaluate(index)

    def __repr__(self) -> str:
        return f"And({self.left!r}, {self.right!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, And):
            return False
        return self.left == other.left and self.right == other.right


class Or(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode) -> None:
        self.left = left
        self.right = right

    def evaluate(self, index: Any) -> set[int]:
        return self.left.evaluate(index) | self.right.evaluate(index)

    def __repr__(self) -> str:
        return f"Or({self.left!r}, {self.right!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Or):
            return False
        return self.left == other.left and self.right == other.right


class Not(ASTNode):
    def __init__(self, operand: ASTNode) -> None:
        self.operand = operand

    def evaluate(self, index: Any) -> set[int]:
        documents: dict[int, Any] = getattr(index, "documents", {})
        all_docs: set[int] = set(documents.keys())
        return all_docs - self.operand.evaluate(index)

    def __repr__(self) -> str:
        return f"Not({self.operand!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Not):
            return False
        return self.operand == other.operand


def parse_query(query: str) -> ASTNode:
    """Простий парсер булевих запитів для AST."""
    tokens = query.replace("(", " ( ").replace(")", " ) ").split()
    if not tokens:
        return Term("")

    def parse_expression(index: int = 0) -> tuple[ASTNode, int]:
        nodes: list[ASTNode] = []
        operators: list[str] = []

        while index < len(tokens):
            token = tokens[index]
            if token == "(":
                sub_node, index = parse_expression(index + 1)
                nodes.append(sub_node)
            elif token == ")":
                break
            elif token in ("AND", "OR"):
                operators.append(token)
                index += 1
            elif token == "NOT":
                index += 1
                if tokens[index] == "(":
                    sub_node, index = parse_expression(index + 1)
                    nodes.append(Not(sub_node))
                else:
                    nodes.append(Not(Term(tokens[index])))
                    index += 1
            elif token.startswith('"') and not token.endswith('"'):
                phrase_tokens = [token.strip('"')]
                index += 1
                while index < len(tokens) and not tokens[index].endswith('"'):
                    phrase_tokens.append(tokens[index])
                    index += 1
                if index < len(tokens):
                    phrase_tokens.append(tokens[index].strip('"'))
                    index += 1
                nodes.append(Phrase(" ".join(phrase_tokens)))
            else:
                nodes.append(Term(token.strip('"')))
                index += 1

        if not nodes:
            return Term(""), index

        root = nodes[0]
        for i, op in enumerate(operators):
            if i + 1 < len(nodes):
                if op == "AND":
                    root = And(root, nodes[i + 1])
                elif op == "OR":
                    root = Or(root, nodes[i + 1])

        return root, index

    node, _ = parse_expression(0)
    return node