from pathlib import Path
import pytest
from findex.index import IndexMapping


@pytest.fixture
def sample_corpus(tmp_path: Path) -> Path:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "doc1.txt").write_text("apple banana orange python", encoding="utf-8")
    (corpus_dir / "doc2.txt").write_text("python testing pytest hypothesis", encoding="utf-8")
    return corpus_dir


@pytest.fixture
def built_index(sample_corpus: Path) -> IndexMapping:
    idx = IndexMapping()
    idx.build_from_corpus(sample_corpus)
    return idx