from findex.builder import IndexMapping
from findex.models import DocMeta, Posting
from findex.query_ast import And, Not, Or, Phrase, Term, parse_query


def test_ast_evaluation() -> None:
    idx = IndexMapping()
    idx.documents[0] = DocMeta(doc_id=0, path="doc1.txt", length=10)
    idx.documents[1] = DocMeta(doc_id=1, path="doc2.txt", length=10)
    
    idx._index["cat"] = [Posting(doc_id=0, tf=1, positions=(0,))]  # type: ignore[reportPrivateUsage]
    idx._index["dog"] = [Posting(doc_id=1, tf=1, positions=(0,))]  # type: ignore[reportPrivateUsage]
    
    node_and = And(Term("cat"), Term("dog"))
    assert node_and.evaluate(idx) == set()
    
    node_or = Or(Term("cat"), Term("dog"))
    assert node_or.evaluate(idx) == {0, 1}
    
    node_not = Not(Term("cat"))
    assert node_not.evaluate(idx) == {1}


def test_phrase_query() -> None:
    idx = IndexMapping()
    idx.documents[0] = DocMeta(doc_id=0, path="doc1.txt", length=10)
    idx._index["quick"] = [Posting(doc_id=0, tf=1, positions=(0,))]  # type: ignore[reportPrivateUsage]
    idx._index["brown"] = [Posting(doc_id=0, tf=1, positions=(1,))]  # type: ignore[reportPrivateUsage]
    
    phrase = Phrase("quick brown")
    assert phrase.evaluate(idx) == {0}


def test_query_parsing() -> None:
    q = parse_query("cat AND dog")
    assert isinstance(q, And)
    assert q.left == Term("cat")
    assert q.right == Term("dog")