from pathlib import Path


def iter_documents(folder_path):
    #Потоково повертає кортежі (filename, text) через yield.
    path = Path(folder_path)
    for file_path in path.glob("*.txt"):
        if file_path.name.startswith("~") or file_path.name.startswith("."):
            continue
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            yield file_path.name, f.read()


def load_all_documents(folder_path):
    #Жадібно зчитує весь корпус файлів у пам'ять.
    path = Path(folder_path)
    docs = []
    for file_path in path.glob("*.txt"):
        if file_path.name.startswith("~") or file_path.name.startswith("."):
            continue
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            docs.append((file_path.name, f.read()))
    return docs