import array
from dataclasses import dataclass
import tracemalloc

# 1. Звичайний dataclass
@dataclass
class RegularPosting:
    doc_id: int
    tf: int

# 2. Dataclass зі slots
@dataclass
class SlottedPosting:
    __slots__ = ("doc_id", "tf")
    doc_id: int
    tf: int

N = 100_000

# Тест 1: Звичайний
tracemalloc.start()
reg_list = [RegularPosting(i, i % 10) for i in range(N)]
_, peak_reg = tracemalloc.get_traced_memory()
tracemalloc.stop()

# Тест 2: Slots
tracemalloc.start()
slot_list = [SlottedPosting(i, i % 10) for i in range(N)]
_, peak_slot = tracemalloc.get_traced_memory()
tracemalloc.stop()

# Тест 3: array('I')
tracemalloc.start()
arr_docs = array.array('I', (i for i in range(N)))
arr_tfs = array.array('I', (i % 10 for i in range(N)))
_, peak_arr = tracemalloc.get_traced_memory()
tracemalloc.stop()

print("=== Замір пам'яті на 100 000 постінгів ===")
print(f"Звичайний dataclass:  {peak_reg / (1024 * 1024):.2f} MB")
print(f"Dataclass зі slots:   {peak_slot / (1024 * 1024):.2f} MB")
print(f"Пари array('I'):      {peak_arr / (1024 * 1024):.2f} MB")