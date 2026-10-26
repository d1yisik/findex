from pathlib import Path
from findex.builder import IndexMapping


def test_build_from_corpus(tmp_path: Path) -> None:
    file1 = tmp_path / "a.txt"
    file1.write_text("python search engine test", encoding="utf-8")
    
    file2 = tmp_path / "b.txt"
    file2.write_text("python testing hypothesis pytest", encoding="utf-8")

    idx = IndexMapping()
    idx.build_from_corpus(tmp_path)

    assert len(idx.documents) == 2
    assert "python" in idx
    assert len(idx["python"]) == 2
    assert idx.avg_doc_length > 0