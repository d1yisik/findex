from __future__ import annotations

import argparse
from pathlib import Path

from findex.builder import open_index
from findex.decorators import cached_search, timed
from findex.query_ast import Term, parse_query
from findex.ranking import BM25, TfIdf, rank_documents
from findex.snippets import make_snippet


def extract_terms(node) -> list[str]:
    from findex.query_ast import And, Not, Or, Phrase, Term
    if isinstance(node, Term):
        return [node.value]
    elif isinstance(node, Phrase):
        return node.words
    elif isinstance(node, (And, Or)):
        return extract_terms(node.left) + extract_terms(node.right)
    elif isinstance(node, Not):
        return []
    return []


@timed
def execute_search(index, query_str: str, scorer_name: str, top_k: int = 5):
    ast_tree = parse_query(query_str)
    matched_docs = ast_tree.evaluate(index)

    if not matched_docs:
        return []

    scorer = BM25(index) if scorer_name.lower() == "bm25" else TfIdf(index)
    query_terms = extract_terms(ast_tree)

    results = rank_documents(index, query_terms, matched_docs, scorer, top_k=top_k)

    for res in results:
        file_path = Path(res.path)
        if not file_path.exists():
            file_path = Path("data") / res.path
        res.snippet = make_snippet(file_path, query_terms)

    return results


def main():
    parser = argparse.ArgumentParser(description="Ранжований пошук з AST-парсером і BM25/TF-IDF.")
    parser.add_argument("index_file", type=str, help="Шлях до index.bin")
    parser.add_argument("query", type=str, help="Запит")
    parser.add_argument(
        "--scorer",
        choices=["bm25", "tfidf"],
        default="bm25",
        help="Модель ранжування (bm25 або tfidf)",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Кількість результатів")

    args = parser.parse_args()

    with open_index(args.index_file) as index:
        print(f"Завантажено індекс: {index}")

        @cached_search(maxsize=32)
        def run_cached(q: str):
            return execute_search(index, q, args.scorer, top_k=args.top_k)

        # Перший запуск
        results = run_cached(args.query)

        print(f"\nРезультати ({args.scorer.upper()}) для запиту: '{args.query}'\n" + "-" * 60)
        for rank, res in enumerate(results, start=1):
            print(f"{rank}. [Score: {res.score:.4f}] {res.path} (Doc ID: {res.doc_id})")
            print(f"   Сніпет: {res.snippet}\n")

        # Другий запуск (демонстрація кешу)
        print("Повторний запуск для перевірки кешу:")
        _ = run_cached(args.query)


if __name__ == "__main__":
    main()