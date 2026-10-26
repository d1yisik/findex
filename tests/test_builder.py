from pathlib import Path

from findex.index import IndexMapping
from findex.models import Posting


def test_index_mapping_dunders() -> None:
    idx = IndexMapping()
    idx._index["python"] = [Posting(doc_id=1, tf=1, positions=(0,))]  # pyright: ignore[reportPrivateUsage]
    assert "python" in idx
    assert "PYTHON" in idx
    assert len(idx) == 1


def test_serialization(tmp_path: Path) -> None:
    idx = IndexMapping()
    idx._index["test"] = [Posting(doc_id=1, tf=2, positions=(1, 5))]  # pyright: ignore[reportPrivateUsage]

    json_file = tmp_path / "test_index.json"
    idx.save_json(json_file)

    loaded_json = IndexMapping.load_json(json_file)
    assert "test" in loaded_json
    assert loaded_json["test"][0].tf == 2

    bin_file = tmp_path / "test_index.bin"
    idx.save_pickle(bin_file)

    loaded_bin = IndexMapping.load_pickle(bin_file)
    assert "test" in loaded_bin
    assert loaded_bin["test"][0].tf == 2