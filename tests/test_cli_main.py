from __future__ import annotations

from pathlib import Path
from _pytest.monkeypatch import MonkeyPatch
import pytest

from findex.cli import main as cli_main
from findex.index import main as index_main
from findex.search import main as search_main


def test_index_and_search_cli_main(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "doc1.txt").write_text("apple banana orange", encoding="utf-8")

    idx_file = tmp_path / "index.json"

    monkeypatch.setattr("sys.argv", ["findex-index", str(corpus_dir), "--out", str(idx_file)])
    index_main()
    assert idx_file.exists()

    monkeypatch.setattr("sys.argv", ["findex-search", "apple", "-i", str(idx_file)])
    try:
        search_main()
    except SystemExit:
        pass


@pytest.mark.parametrize(
    "query",
    ["apple", "banana", "apple AND banana", "apple OR orange", "NOT banana"],
)
def test_search_queries_cli(tmp_path: Path, monkeypatch: MonkeyPatch, query: str) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "doc1.txt").write_text("apple banana orange", encoding="utf-8")

    idx_file = tmp_path / "index.bin"

    monkeypatch.setattr("sys.argv", ["findex-index", str(corpus_dir), "--out", str(idx_file)])
    index_main()

    monkeypatch.setattr("sys.argv", ["findex-search", query, "-i", str(idx_file)])
    try:
        search_main()
    except SystemExit:
        pass


def test_cli_help(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["findex", "--help"])
    try:
        cli_main()
    except SystemExit:
        pass