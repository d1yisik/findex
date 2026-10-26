from __future__ import annotations


def highlight_snippet(text: str, terms: list[str], window: int = 80) -> str:
    """Генерує сніпет із підсвіткою слів."""
    text_lower = text.lower()
    first_pos = -1

    for term in terms:
        pos = text_lower.find(term.lower())
        if pos != -1 and (first_pos == -1 or pos < first_pos):
            first_pos = pos

    if first_pos == -1:
        return text[: window * 2] + "..." if len(text) > window * 2 else text

    start = max(0, first_pos - window)
    end = min(len(text), first_pos + window)
    snippet = text[start:end]

    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet