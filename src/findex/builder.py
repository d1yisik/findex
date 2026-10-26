from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from findex.corpus import read_corpus
from findex.index import IndexMapping
from findex.models import Posting
from findex.tokenizer import tokenize

ExecutorType = Literal["serial", "threads", "processes"]

__all__ = ["build_index_parallel", "ExecutorType", "IndexMapping"]


def _process_single_file(file_path: Path, doc_id: int) -> tuple[int, dict[str, list[int]]]:
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    tokens = tokenize(content)
    positions_map: dict[str, list[int]] = {}
    for pos, token in enumerate(tokens):
        if token not in positions_map:
            positions_map[token] = []
        positions_map[token].append(pos)
    return doc_id, positions_map


def _process_single_file_wrapper(args: tuple[Path, int]) -> tuple[int, dict[str, list[int]]]:
    file_path, doc_id = args
    return _process_single_file(file_path, doc_id)


def _thread_worker(item: tuple[Path, int]) -> tuple[int, dict[str, list[int]]]:
    return _process_single_file(item[0], item[1])


def build_index_parallel(
    corpus_dir: Path,
    workers: int = 4,
    executor_type: ExecutorType = "processes",
) -> IndexMapping:
    idx = IndexMapping()
    corpus_files: list[Path] = read_corpus(corpus_dir)

    for doc_id, file_path in enumerate(corpus_files, start=1):
        idx.doc_titles[doc_id] = str(file_path)

    tasks: list[tuple[Path, int]] = [(fp, doc_id) for doc_id, fp in enumerate(corpus_files, start=1)]
    results: list[tuple[int, dict[str, list[int]]]] = []

    if executor_type == "serial" or workers <= 1:
        results = [_process_single_file(fp, doc_id) for doc_id, fp in enumerate(corpus_files, start=1)]
    elif executor_type == "threads":
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(_thread_worker, tasks))
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(_process_single_file_wrapper, tasks))

    for doc_id, pos_map in results:
        for term, positions in pos_map.items():
            posting = Posting(doc_id=doc_id, tf=len(positions), positions=tuple(positions))
            idx.add_posting(term, posting)

    return idx