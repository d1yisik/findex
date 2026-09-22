import argparse
import time
import tracemalloc
from pathlib import Path

from findex.builder import InvertedIndex


def main():
    parser = argparse.ArgumentParser(
        description="Построение инвертированного индекса."
    )
    parser.add_argument(
        "corpus_dir", type=str, help="Путь к папке с документами (.txt)"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="index.bin",
        help="Путь сохранения файла индекса",
    )
    parser.add_argument(
        "--format",
        choices=["pickle", "json"],
        default="pickle",
        help="Формат сериализации",
    )

    args = parser.parse_args()

    # Запускаем трекинг памяти и таймер
    tracemalloc.start()
    start_time = time.perf_counter()

    index = InvertedIndex()
    index.build_from_corpus(args.corpus_dir)

    out_path = Path(args.out)
    if args.format == "json":
        index.save_json(out_path)
    else:
        index.save_pickle(out_path)

    elapsed_time = time.perf_counter() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    file_size_kb = out_path.stat().st_size / 1024

    print(f"Индексация завершена успешно!")
    print(f"Документов: {len(index.documents)}")
    print(f"Уникальных терминов: {len(index.index)}")
    print(f"Файл сохранен в: {out_path} ({file_size_kb:.2f} KB)")
    print(f"Время выполнения: {elapsed_time:.4f} сек")
    print(f"Пик памяти: {peak / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()