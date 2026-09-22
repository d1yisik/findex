from __future__ import annotations

import argparse
import sys
import tracemalloc

from findex.builder import Index
from findex.decorators import timed


@timed
def build_and_save(corpus_dir: str, output_path: str):
    idx = Index()
    idx.build_from_corpus(corpus_dir)
    idx.save_pickle(output_path)
    return idx


def main():
    parser = argparse.ArgumentParser(description="Індексація корпусу документів.")
    parser.add_argument("corpus_dir", type=str, help="Шлях до папки з документами")
    parser.add_argument("--out", type=str, default="index.bin", help="Шлях для збереження індексу")

    args = parser.parse_args()

    tracemalloc.start()
    idx = build_and_save(args.corpus_dir, args.out)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Індексація завершена успішно!")
    print(f"Індекс: {idx}")
    print(f"Унікальних термінів: {len(idx)}")
    print(f"Документів: {idx.num_docs}")
    print(f"Середня довжина документу: {idx.avg_doc_length:.2f} токенів")
    print(f"Пікове споживання пам'яті: {peak / 1024:.2f} KB")


if __name__ == "__main__":
    main()