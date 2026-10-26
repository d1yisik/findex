from pathlib import Path
from findex.builder import IndexMapping
from findex.corpus import iter_documents
from findex.decorators import cached
from findex.models import DocMeta, Posting
from findex.search import search_query


def test_iter_documents(tmp_path: Path) -> None:
    doc1 = tmp_path / "doc1.txt"
    doc1.write_text("hello world", encoding="utf-8")
    
    docs = list(iter_documents(tmp_path))
    assert len(docs) == 1
    assert docs[0][1] == "hello world"


def test_search_query_with_cache() -> None:
    idx = IndexMapping()
    idx.documents[0] = DocMeta(doc_id=0, path="doc1.txt", length=5)
    idx._index["hello"] = [Posting(doc_id=0, tf=1, positions=(0,))]  # pyright: ignore[reportPrivateUsage]
    
    res1 = search_query(idx, "hello", engine="bm25")
    res2 = search_query(idx, "hello", engine="bm25")
    assert res1 == res2


def test_cached_decorator() -> None:
    call_count = 0

    @cached
    def add(a: int, b: int) -> int:
        nonlocal call_count
        call_count += 1
        return a + b

    assert add(1, 2) == 3
    assert add(1, 2) == 3
    assert call_count == 1