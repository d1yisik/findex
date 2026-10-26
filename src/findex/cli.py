# pyright: reportUnknownVariableType=none
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownArgumentType=none
# pyright: reportAttributeAccessIssue=none

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

from rich.live import Live
from rich.table import Table
import typer
import uvicorn

from findex.builder import ExecutorType, build_index_parallel
from findex.crawler import AsyncCrawler
from findex.search_engine import SearchEngine, SearchResult

app = typer.Typer(help="Findex: A simple text search engine CLI")


@app.command(name="serve")
def serve(
    port: int = typer.Option(8000, "--port", "-p", help="Port to run server on"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of worker processes"),
) -> None:
    """Start the FastAPI web server."""
    uvicorn.run("findex.web.app:app", host="0.0.0.0", port=port, workers=workers, reload=False)


@app.command(name="crawl")
def crawl(
    url: str = typer.Argument(..., help="Start URL to crawl"),
    out: Path = typer.Option(Path("corpus.jsonl"), "--out", "-o", help="Output JSONL corpus file"),
    max_pages: int = typer.Option(200, "--max-pages", "-m", help="Maximum pages to collect"),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="Max concurrent requests"),
    log_file: Path = typer.Option(Path("crawl.log"), "--log-file", help="Path to log file"),
) -> None:
    """Async crawler with rich progress reporting and JSONL output."""
    async def _run_crawl():
        crawler = AsyncCrawler(start_urls=[url], max_pages=max_pages, max_concurrency=concurrency)
        start_time = time.monotonic()

        log_handle = log_file.open("w", encoding="utf-8")
        jsonl_handle = out.open("w", encoding="utf-8")

        def make_table() -> Table:
            elapsed = max(time.monotonic() - start_time, 0.1)
            pages_per_sec = crawler.pages_crawled / elapsed
            table = Table(title="Findex Async Crawler (Lab 06)")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="bold green")
            table.add_row("Pages Collected", str(crawler.pages_crawled))
            table.add_row("Pages / sec", f"{pages_per_sec:.2f}")
            table.add_row("Active Requests", str(crawler.active_requests))
            table.add_row("Error Count", str(crawler.error_count))
            table.add_row("Queue Depth", str(crawler.queue.qsize()))
            return table

        with Live(make_table(), refresh_per_second=4) as live:
            async for page in crawler.crawl_stream():
                log_entry = f"URL: {page.url} | Status: {page.status_code} | Time: {page.elapsed_time:.3f}s | Error: {page.error}\n"
                log_handle.write(log_entry)
                log_handle.flush()

                if page.status_code == 200 and page.text:
                    record = {
                        "url": page.url,
                        "status": page.status_code,
                        "text": page.text,
                        "elapsed": page.elapsed_time,
                    }
                    jsonl_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    jsonl_handle.flush()

                live.update(make_table())

        log_handle.close()
        jsonl_handle.close()

    asyncio.run(_run_crawl())


@app.command(name="index")
def index(
    corpus: Path = typer.Argument(..., help="Path to corpus directory or jsonl file"),
    out: Path = typer.Option(Path("index.json"), "--out", "-o", help="Output index file"),
    workers: int = typer.Option(os.cpu_count() or 4, "--workers", "-w", help="Number of worker threads/processes"),
    executor: ExecutorType = typer.Option("processes", "--executor", "-e", help="Execution mode: serial, threads, processes"),
) -> None:
    """Build inverted index from corpus with parallel execution support."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not corpus.exists():
        logging.error("Corpus path does not exist: %s", corpus)
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


@app.command(name="search")
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


def index_main() -> None:
    try:
        typer.run(index)
    except SystemExit as e:
        code = getattr(e, "code", 0)
        if code != 0 and code is not None:
            raise


def search_main() -> None:
    try:
        typer.run(search)
    except SystemExit as e:
        code = getattr(e, "code", 0)
        if code != 0 and code is not None:
            raise


def main() -> None:
    try:
        app()
    except SystemExit as e:
        code = getattr(e, "code", 0)
        if code != 0 and code is not None:
            raise


if __name__ == "__main__":
    main()