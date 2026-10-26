from __future__ import annotations

import argparse
from pathlib import Path

from findex.builder import IndexMapping


def main() -> None:
    parser = argparse.ArgumentParser(description="findex index builder")
    parser.add_argument("corpus", type=Path, help="Corpus directory path")
    parser.add_argument("--out", "-o", type=Path, default=Path("index.bin"), help="Output index file path")
    args = parser.parse_args()

    idx = IndexMapping()
    idx.build_from_corpus(args.corpus)

    if args.out.suffix == ".json":
        idx.save_json(args.out)
    else:
        idx.save_pickle(args.out)

    print(f"Indexed documents: {len(idx.documents)}, total terms: {len(idx)}")


if __name__ == "__main__":
    main()