import time
import tracemalloc
from pathlib import Path
from findex.builder import InvertedIndex
from findex.search_engine import BooleanSearchEngine

DATA_DIR = "data"
BIN_FILE = "index.bin"
JSON_FILE = "index.json"

# 1. Замір індексації та збереження
idx = InvertedIndex()
idx.build_from_corpus(DATA_DIR)

# Pickle
t0 = time.perf_counter()
idx.save_pickle(BIN_FILE)
t_save_pickle = time.perf_counter() - t0

t0 = time.perf_counter()
_ = InvertedIndex.load_pickle(BIN_FILE)
t_load_pickle = time.perf_counter() - t0

size_pickle = Path(BIN_FILE).stat().st_size

# JSON
t0 = time.perf_counter()
idx.save_json(JSON_FILE)
t_save_json = time.perf_counter() - t0

t0 = time.perf_counter()
_ = InvertedIndex.load_json(JSON_FILE)
t_load_json = time.perf_counter() - t0

size_json = Path(JSON_FILE).stat().st_size

print("=== 1. Серіалізація (Save / Load) ===")
print(f"Pickle | Розмір: {size_pickle} B | Save: {t_save_pickle*1000:.3f} ms | Load: {t_load_pickle*1000:.3f} ms")
print(f"JSON   | Розмір: {size_json} B | Save: {t_save_json*1000:.3f} ms | Load: {t_load_json*1000:.3f} ms\n")

# 2. Бенчмарк пошуку (Merge vs Set)
# Вибираємо терміни за частотою зустрічальності в документах
sorted_terms = sorted(idx.index.keys(), key=lambda t: len(idx.index[t]), reverse=True)
frequent_terms = sorted_terms[:2]
rare_terms = sorted_terms[-2:]

test_queries = frequent_terms + rare_terms
engine_merge = BooleanSearchEngine(idx, engine="merge")
engine_set = BooleanSearchEngine(idx, engine="set")

print("=== 2. Бенчмарк пошуку (Merge vs Set) ===")
print(f"{'Термін':<15} | {'Тип':<10} | {'Merge (ms)':<12} | {'Set (ms)':<12}")
print("-" * 55)

for term in test_queries:
    t_type = "Frequent" if term in frequent_terms else "Rare"
    
    # Замір Merge (1000 ітерацій для стабільності)
    t0 = time.perf_counter()
    for _ in range(1000):
        engine_merge.search(term)
    dt_merge = (time.perf_counter() - t0)

    # Замір Set (1000 ітерацій)
    t0 = time.perf_counter()
    for _ in range(1000):
        engine_set.search(term)
    dt_set = (time.perf_counter() - t0)

    print(f"{term:<15} | {t_type:<10} | {dt_merge:.4f} ms    | {dt_set:.4f} ms")