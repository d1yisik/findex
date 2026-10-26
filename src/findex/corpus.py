from pathlib import Path


def read_corpus(corpus_dir: Path) -> list[Path]:
    """Reads and returns a sorted list of file paths from the corpus directory."""
    if not corpus_dir.exists() or not corpus_dir.is_dir():
        return []
    return sorted([p for p in corpus_dir.rglob("*") if p.is_file() and not p.name.startswith(".")])


def iter_documents(corpus_dir: Path) -> list[tuple[Path, str]]:
    """Reads corpus directory and returns a list of (file_path, content) tuples for tests."""
    files = read_corpus(corpus_dir)
    return [(p, p.read_text(encoding="utf-8", errors="ignore")) for p in files]