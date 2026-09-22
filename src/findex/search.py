import argparse
import time
import tracemalloc
from pathlib import Path

from findex.builder import InvertedIndex
from findex.search_engine import BooleanSearchEngine


def main():
    parser = argparse.ArgumentParser(description="Пошук у побудованому індексі.")
    parser.add_argument("index_file", type=str, help="Шлях до збереженого index.bin")
    parser.add_argument("query", type=str, help="Пошуковий запит (напр. 'term1 term2')")
    parser.add_argument(
        "--engine",
        choices=["merge", "set"],
        default="merge",
        help="Алгоритм пошуку (merge або set)",
    )
    parser.add_argument(
        "--format",
        choices=["pickle", "json"],
        default="pickle",
        help="Формат зчитування індексу",
    )

    args = parser.parse_args()

    # Завантаження індексу
    if args.format == "json":
        index = InvertedIndex.load_json(args.index_file)
    else:
        index = InvertedIndex.load_pickle(args.index_file)

    tracemalloc.start()
    start_time = time.perf_counter()

    engine = BooleanSearchEngine(index, engine=args.engine)
    results = engine.search(args.query)

    elapsed_time = time.perf_counter() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Рушій: {args.engine.upper()} | Знайдено документів: {len(results)}")
    print(f"Час пошуку: {elapsed_time * 1000:.4f} мс")
    print(f"Пік пам'яті: {peak / 1024:.2f} KB\n")

    for doc_id in results:
        meta = index.documents.get(doc_id)
        if meta:
            print(f" - [ID: {doc_id}] {meta.path} (довжина: {meta.length} токенів)")


if __name__ == "__main__":
    main()