from __future__ import annotations

from pathlib import Path
import re


def highlight_term(text: str, term: str) -> str:
    """Підсвічує знайдений термін жовтим кольором у консолі."""
    pattern = re.compile(rf"\b({re.escape(term)})\b", re.IGNORECASE)
    return pattern.sub(r"\033[1;33m**\1**\033[0m", text)


def make_snippet(file_path: str | Path, terms: list[str], window: int = 80) -> str:
    """Створює сніпет навколо найкращого збігу з вікном ±80 символів."""
    p = Path(file_path)
    
    # Спроба знайти файл за кількома типовими шляхами
    candidates = [p, Path("data") / p.name, Path("data") / p]
    target_path = None
    for cand in candidates:
        if cand.exists() and cand.is_file():
            target_path = cand
            break

    if target_path is None:
        return f"[Текст файлу {p.name} недоступний]"

    with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read().strip()

    if not content:
        return "[Порожній документ]"

    best_pos = -1
    matched_term = ""

    for term in terms:
        m = re.search(rf"\b{re.escape(term)}\b", content, re.IGNORECASE)
        if m:
            best_pos = m.start()
            matched_term = term
            break

    if best_pos == -1:
        snippet = content[: window * 2].strip()
        if len(content) > window * 2:
            snippet += "..."
    else:
        start = max(0, best_pos - window)
        end = min(len(content), best_pos + len(matched_term) + window)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(content) else ""
        snippet = f"{prefix}{content[start:end].strip()}{suffix}"

    for term in terms:
        snippet = highlight_term(snippet, term)

    return snippet