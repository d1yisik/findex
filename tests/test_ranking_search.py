from findex.builder import IndexMapping
from findex.models import DocMeta, Posting
from findex.ranking import BM25, TfIdf, rank_documents
from findex.search_engine import BooleanSearchEngine
from findex.snippets import highlight_snippet


def test_ranking_and_snippets() -> None:
    idx = IndexMapping()
    idx.documents[0] = DocMeta(doc_id=0, path="doc1.txt", length=5)
    idx._index["test"] = [Posting(doc_id=0, tf=2, positions=(0, 2))]  # pyright: ignore[reportPrivateUsage]
    
    bm25 = BM25(idx)
    score_bm25 = bm25.score_term("test", tf=2, doc_len=5)
    assert score_bm25 > 0

    tfidf = TfIdf(idx)
    score_tfidf = tfidf.score_term("test", tf=2, doc_len=5)
    assert score_tfidf > 0

    results = rank_documents(idx, ["test"], {0}, bm25)
    assert len(results) == 1
    assert results[0].doc_id == 0

    snippet = highlight_snippet("This is a test snippet text", ["test"])
    assert "test" in snippet


def test_boolean_search_engine() -> None:
    idx = IndexMapping()
    idx.documents[0] = DocMeta(doc_id=0, path="doc1.txt", length=5)
    idx._index["hello"] = [Posting(doc_id=0, tf=1, positions=(0,))]  # pyright: ignore[reportPrivateUsage]
    
    engine_set = BooleanSearchEngine(idx, engine="set")
    assert engine_set.search("hello") == [0]

    engine_merge = BooleanSearchEngine(idx, engine="merge")
    assert engine_merge.search("hello") == [0]