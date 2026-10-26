from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from findex.builder import IndexMapping
from findex.ranking import BM25, TfIdf, rank_documents

app = typer.Typer(help="findex CLI search engine tool", add_completion=False)
err_console = Console(stderr=True)
out_console = Console()


def setup_logging(verbose: int) -> None:
    logger = logging.getLogger("findex")
    if verbose == 1:
        logger.setLevel(logging.INFO)
    elif verbose >= 2:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.handlers.clear()
    logger.addHandler(handler)


@app.command()
def index(
    corpus_dir: Path = typer.Argument(..., help="Path to corpus directory"),
    output: Path = typer.Option(
        Path("index.json"), "--output", "-o", help="Output index file"
    ),
    verbose: int = typer.Option(
        0, "--verbose", "-v", count=True, help="Verbosity level"
    ),
) -> None:
    """Build index from text files."""
    setup_logging(verbose)
    if not corpus_dir.is_dir():
        err_console.print(f"Error: Corpus directory '{corpus_dir}' does not exist.")
        raise typer.Exit(code=1)

    idx = IndexMapping()
    idx.build_from_corpus(corpus_dir)
    if output.suffix == ".bin":
        idx.save_pickle(output)
    else:
        idx.save_json(output)
    err_console.print(f"Successfully indexed documents into {output}")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query string"),
    index_file: Path = typer.Option(
        Path("index.json"), "--index", "-i", help="Index file path"
    ),
    engine: str = typer.Option("bm25", "--engine", "-e", help="Scoring engine"),
    json_out: bool = typer.Option(False, "--json", help="Output results as JSON"),
    verbose: int = typer.Option(
        0, "--verbose", "-v", count=True, help="Verbosity level"
    ),
) -> None:
    """Search for query in index."""
    setup_logging(verbose)
    if not index_file.exists():
        err_console.print(f"Error: Index file '{index_file}' not found.")
        raise typer.Exit(code=1)

    idx = IndexMapping.load_json(index_file) if index_file.suffix == ".json" else IndexMapping.load_pickle(index_file)
    terms = query.lower().split()
    matched_docs = set(idx.documents.keys())

    scorer_obj = BM25(idx) if engine == "bm25" else TfIdf(idx)
    results = rank_documents(idx, terms, matched_docs, scorer_obj)

    if json_out:
        data = [{"doc_id": r.doc_id, "path": r.path, "score": r.score} for r in results]
        out_console.print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Search Results for '{query}' ({engine})")
    table.add_column("Doc ID", justify="right", style="cyan")
    table.add_column("Path", style="magenta")
    table.add_column("Score", justify="right", style="green")

    for r in results:
        table.add_row(str(r.doc_id), r.path, str(r.score))

    out_console.print(table)


@app.command()
def stats(
    index_file: Path = typer.Option(
        Path("index.json"), "--index", "-i", help="Index file path"
    ),
    verbose: int = typer.Option(
        0, "--verbose", "-v", count=True, help="Verbosity level"
    ),
) -> None:
    """Show index statistics."""
    setup_logging(verbose)
    if not index_file.exists():
        err_console.print(f"Error: Index file '{index_file}' not found.")
        raise typer.Exit(code=1)

    idx = IndexMapping.load_json(index_file) if index_file.suffix == ".json" else IndexMapping.load_pickle(index_file)
    err_console.print(f"Terms: {len(idx)}, Documents: {len(idx.documents)}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()