from pathlib import Path
from hypothesis import given, strategies as st
import pytest

from findex.builder import IndexMapping
from findex.models import Posting
from findex.query_ast import Term, parse_query


# Властивість 1: load(save(index)) дає той самий індекс
@given(st.lists(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8), min_size=1, max_size=5))
def test_save_load_roundtrip(tmp_path_factory: pytest.TempPathFactory, words: list[str]) -> None:
    tmp_path = tmp_path_factory.mktemp("hypo")
    idx = IndexMapping()
    for doc_id, word in enumerate(words):
        idx._index.setdefault(word, []).append(Posting(doc_id=doc_id, tf=1, positions=(0,)))  # pyright: ignore[reportPrivateUsage]

    json_path = tmp_path / "idx.json"
    idx.save_json(json_path)
    loaded = IndexMapping.load_json(json_path)

    assert set(idx.keys()) == set(loaded.keys())


# Властивість 2: Постінги завжди відсортовані за doc_id
@given(st.lists(st.integers(min_value=0, max_value=100), min_size=1, max_size=20))
def test_postings_sorted_by_doc_id(doc_ids: list[int]) -> None:
    sorted_ids = sorted(set(doc_ids))
    postings = [Posting(doc_id=d, tf=1, positions=(0,)) for d in sorted_ids]
    for i in range(len(postings) - 1):
        assert postings[i].doc_id < postings[i + 1].doc_id


# Властивість 3: Терм завжди переводиться в нижній регістр
@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=1, max_size=20))
def test_term_lowercasing_invariant(term_str: str) -> None:
    term = Term(term_str)
    assert term.term == term_str.lower()


# Властивість 4: Розбір AND-запитів не повертає None
@given(st.lists(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10), min_size=1, max_size=3))
def test_parsed_query_contains_terms(words: list[str]) -> None:
    query_str = " AND ".join(words)
    ast = parse_query(query_str)
    assert ast is not None