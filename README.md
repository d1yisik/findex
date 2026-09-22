# findex — Інвертований індекс та ранжований пошук (Лабораторна робота №3)

Розширення пошукового рушія `findex`: повноцінна модель даних Python (dunder-методи, Mapping), контекстні менеджери, взаємозамінні моделі ранжування (TF-IDF / BM25) через протокол `Scorer`, AST-парсер складних запитів рекурсивним спуском, декоратори заміру часу й кешування та генерація сніпетів.

---

## Архітектура та нові модулі

- `src/findex/models.py` — моделі даних `Posting` (з позиціями для фразового пошуку), `DocMeta` та `SearchResult` (з підтримкою сортування `order=True`).
- `src/findex/builder.py` — клас `Index` (наслідує `collections.abc.Mapping`), реалізує dunder-методи (`__len__`, `__getitem__`, `__contains__`, `__iter__`, `__repr__`), `cached_property` для `avg_doc_length` та контекстний менеджер `open_index(path)`.
- `src/findex/ranking.py` — протокол `Scorer` (duck typing), моделі ранжування `TfIdf` та `BM25(k1=1.5, b=0.75)`, відбір топ-k через `heapq.nlargest`.
- `src/findex/query_ast.py` — AST-парсер рекурсивного спуску з підтримкою дужок, лапок, операторів `AND`, `OR`, `NOT` та вузлами `Term`, `Phrase`, `And`, `Or`, `Not` з підтримкою синтаксису `&`, `|`, `~`.
- `src/findex/snippets.py` — генерація сніпетів із вікном ±80 символів навколо збігу та термінальною підсвіткою слів.
- `src/findex/decorators.py` — декоратор `@timed` (з `functools.wraps`) та кешування запитів `@cached_search` на базі `@lru_cache` з фіксацією попадань у кеш.
- `lab3_eval.py` — скрипт перевірки валідності дерева AST, 3 sanity-check для ранжування та розрахунку таблиці Precision@5.

---

## Використання

### 1. Індексація корпусу
```bash
PYTHONPATH=src python3 -m findex.index data/ --out index.bin