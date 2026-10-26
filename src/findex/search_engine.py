# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnnecessaryCast=false

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

from findex.index import IndexMapping
from findex.search import search_query


@dataclass
class SearchResult:
    doc_path: str
    score: float


class SearchEngine:
    def __init__(self, index_or_path: Union[IndexMapping, Path, str], engine: str = "ranked") -> None:
        self.engine: str = engine
        if isinstance(index_or_path, IndexMapping):
            self.index: IndexMapping = index_or_path
        else:
            path = Path(index_or_path)
            if path.suffix == ".json":
                self.index = IndexMapping.load_json(path)
            else:
                self.index = IndexMapping.load_pickle(path)

    def search(self, query: str) -> Union[list[SearchResult], list[int]]:
        raw_results: Any = search_query(self.index, query)
        if not raw_results:
            return []

        if self.engine in ("set", "merge", "boolean"):
            doc_ids: list[int] = []
            for item in raw_results:
                if isinstance(item, int):
                    doc_ids.append(item)
                elif hasattr(item, "doc_id"):
                    val = getattr(item, "doc_id")
                    if isinstance(val, int):
                        doc_ids.append(val)
                    elif isinstance(val, str) and val.isdigit():
                        doc_ids.append(int(val))
                elif hasattr(item, "doc_path"):
                    val = getattr(item, "doc_path")
                    if isinstance(val, int):
                        doc_ids.append(val)
                    elif isinstance(val, str) and val.isdigit():
                        doc_ids.append(int(val))
                elif isinstance(item, (tuple, list)) and len(item) > 0:
                    first = item[0]
                    if isinstance(first, int):
                        doc_ids.append(first)
                    elif isinstance(first, str) and first.isdigit():
                        doc_ids.append(int(first))
            return doc_ids

        results: list[SearchResult] = []
        for item in raw_results:
            doc_path: str = ""
            score: float = 0.0

            if hasattr(item, "doc_path") and hasattr(item, "score"):
                doc_path = str(getattr(item, "doc_path"))
                score = float(getattr(item, "score"))
            elif isinstance(item, (tuple, list)) and len(item) >= 2:
                doc_path_val = item[0]
                score_val = item[1]
                doc_path = str(doc_path_val)
                score = float(score_val)
                if doc_path.isdigit() and int(doc_path) in self.index.doc_titles:
                    doc_path = self.index.doc_titles[int(doc_path)]
            elif hasattr(item, "doc_id"):
                doc_id = getattr(item, "doc_id")
                score_attr = getattr(item, "score", 0.0)
                score = float(score_attr)
                if isinstance(doc_id, int):
                    doc_path = self.index.doc_titles.get(doc_id, str(doc_id))
                else:
                    doc_path = str(doc_id)

            results.append(SearchResult(doc_path=doc_path, score=score))

        return results


BooleanSearchEngine = SearchEngine