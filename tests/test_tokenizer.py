from __future__ import annotations

import pytest
from findex.tokenizer import tokenize


def test_basic_tokenization() -> None:
    text = "Hello, World! This is a TEST-string."
    tokens = tokenize(text)
    assert "hello" in tokens
    assert "world" in tokens


def test_empty_string() -> None:
    assert tokenize("") == []


def test_cyrillic_text() -> None:
    tokens = tokenize("Це тестовий документ українською мовою!")
    assert "тестовий" in tokens
    assert "документ" in tokens


@pytest.mark.parametrize(
    ("input_text", "expected"),
    [
        ("Hello World!", ["hello", "world"]),
        ("Python 3.14 testing...", ["python", "3", "14", "testing"]),
        ("Привіт, всесвіт!", ["привіт", "всесвіт"]),
        ("  ", []),
        ("Special @#$ %^& chars", ["special", "chars"]),
        ("Fast search 100%", ["fast", "search", "100"]),
        ("UPPERCASE lowercase", ["uppercase", "lowercase"]),
        ("one, two, three!", ["one", "two", "three"]),
        ("line1\nline2\ttab", ["line1", "line2", "tab"]),
        ("word-with-hyphen", ["word", "with", "hyphen"]),
    ],
)
def test_tokenize_parametrized(input_text: str, expected: list[str]) -> None:
    assert tokenize(input_text) == expected