import sys
from pathlib import Path
from collections import Counter
import tracemalloc

# Додаємо src до шляхів пошуку модулів
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from findex.corpus import iter_documents
from findex.tokenizer import tokenize

tracemalloc.start()

docs_count = 0
tokens_count = 0
vocab = Counter()

data_path = Path(__file__).resolve().parent / "data"

for filename, content in iter_documents(data_path):
    tokens = tokenize(content)
    docs_count += 1
    tokens_count += len(tokens)
    vocab.update(tokens)

_, peak_mem = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"Документів: {docs_count}")
print(f"Токенів: {tokens_count}")
print(f"Унікальних слів: {len(vocab)}")
print(f"Пікова пам'ять: {peak_mem / 1024:.2f} KB")