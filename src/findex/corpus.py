from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path


def iter_documents(folder_path: str | Path) -> Iterator[tuple[str, str]]:
    """Потоково повертає кортежі (filename, text) через yield."""
    path = Path(folder_path)
    for file_path in path.glob("*.txt"):
        if file_path.name.startswith("~") or file_path.name.startswith("."):
            continue
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            yield file_path.name, f.read()


def load_all_documents(folder_path: str | Path) -> list[tuple[str, str]]:
    """Жадібно зчитує весь корпус файлів у пам'ять."""
    path = Path(folder_path)
    docs: list[tuple[str, str]] = []
    for file_path in path.glob("*.txt"):
        if file_path.name.startswith("~") or file_path.name.startswith("."):
            continue
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            docs.append((file_path.name, f.read()))
    return docs