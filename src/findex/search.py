from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from findex.builder import IndexMapping
from findex.decorators import cached
from findex.models import SearchResult
from findex.query_ast import parse_query
from findex.ranking import BM25, TfIdf, rank_documents


@cached
def search_query(idx: IndexMapping, query: str, engine: str = "bm25") -> list[SearchResult]:
    ast = parse_query(query)
    matched = ast.evaluate(idx)
    terms = [t.lower() for t in query.replace('"', "").split() if t not in ("NOT", "AND", "OR")]
    scorer_obj: Any = BM25(idx) if engine == "bm25" else TfIdf(idx)
    return rank_documents(idx, terms, matched, scorer_obj)


def main() -> None:
    parser = argparse.ArgumentParser(description="findex search tool")
    parser.add_argument("query", type=str, help="Search query string")
    parser.add_argument("--index", "-i", type=Path, default=Path("index.json"), help="Index file path")
    parser.add_argument("--engine", "-e", type=str, default="bm25", help="Scoring engine (bm25 | tfidf)")
    args = parser.parse_args()

    idx = IndexMapping.load_json(args.index) if args.index.suffix == ".json" else IndexMapping.load_pickle(args.index)
    results = search_query(idx, args.query, args.engine)

    for r in results:
        print(f"Doc ID: {r.doc_id} | Path: {r.path} | Score: {r.score}")


if __name__ == "__main__":
    main()