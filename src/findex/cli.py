import logging
import os
from pathlib import Path

import typer

from findex.builder import ExecutorType, build_index_parallel
from findex.search_engine import SearchEngine, SearchResult

app = typer.Typer(help="Findex: A simple text search engine CLI")


@app.command()
def index(
    corpus: Path = typer.Argument(..., help="Path to corpus directory"),
    out: Path = typer.Option(Path("index.json"), "--out", "-o", help="Output index file"),
    workers: int = typer.Option(os.cpu_count() or 4, "--workers", "-w", help="Number of worker threads/processes"),
    executor: ExecutorType = typer.Option("processes", "--executor", "-e", help="Execution mode: serial, threads, processes"),
) -> None:
    """Build inverted index from corpus with parallel execution support."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not corpus.exists() or not corpus.is_dir():
        logging.error("Corpus directory does not exist: %s", corpus)
        raise typer.Exit(code=1)

    try:
        logging.info("Building index using %s executor with %d workers...", executor, workers)
        idx = build_index_parallel(corpus, workers=workers, executor_type=executor)

        if out.suffix == ".json":
            idx.save_json(out)
        else:
            idx.save_pickle(out)

        logging.info("Index successfully saved to %s (%d documents indexed)", out, len(idx.doc_titles))
    except Exception as e:
        logging.error("Worker failed with exception: %s", e, exc_info=True)
        raise typer.Exit(code=1) from e


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    index_path: Path = typer.Option(Path("index.json"), "--index", "-i", help="Path to index file"),
) -> None:
    """Search the index for a query."""
    if not index_path.exists():
        raise typer.Exit(code=1)

    try:
        engine = SearchEngine(index_path)
        results = engine.search(query)
        for res in results:
            if isinstance(res, SearchResult):
                print(f"{res.doc_path}: {res.score}")
            else:
                print(f"{res}")
    except Exception as e:
        logging.error("Search error: %s", e)
        raise typer.Exit(code=1) from e


def main() -> None:
    try:
        typer.run(index)
    except SystemExit as e:
        if e.code != 0 and e.code is not None:
            raise


def search_main() -> None:
    try:
        typer.run(search)
    except SystemExit as e:
        if e.code != 0 and e.code is not None:
            raise


if __name__ == "__main__":
    main()